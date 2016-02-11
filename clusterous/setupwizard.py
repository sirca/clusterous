# Copyright 2015 Nicta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tabulate

from clusterousconfig import AWSConfig
import clusterousconfig
from terminalio import WizardIO
import terminalio

def _retry_input(input_func, max_tries=3):
    def retry(*args, **kwargs):
        count = 0
        retval = {}
        while count <= max_tries:
            retval = input_func(*args, **kwargs)
            if not retval or retval['status'] == 'fail':
                WizardIO.out(retval['message'], error=True)
            else:
                if retval['status'] == 'cancel':
                    WizardIO.out('Cancelled')
                return retval
            count += 1

        if count > max_tries:
            WizardIO.out('Failing after {0} tries'.format(count), error=True)
        return retval
    return retry



class AWSSetup:

    def _quit_setup(self):
        WizardIO.new_para()
        WizardIO.out('Quiting Clusterous setup', bold=True)
        return False


    def start(self):
        try:
            aws_config = AWSConfig()
            WizardIO.out('Welcome to Clusterous setup')
            if not aws_config.get_current_profile():
                # No current config
                WizardIO.out('This guide will configure Clusterous to allow you to use it with Amazon Web Services', indent=2)
                WizardIO.out('You only need to run this the first time you use Clusterous', indent=2)
            else:
                WizardIO.out('This guide will help you create a new configuration profile for using Clusterous with Amazon Web Services', indent=2)

            config = {}
            
            WizardIO.new_para()
            WizardIO.out("Clusterous needs your AWS account's access keys", indent=2, bold=True)
            results = self._enter_aws_keys(config)
            
            if results['status'] == 'success':
                WizardIO.out('Credentials validated')
            else:
                return self._quit_setup()

            WizardIO.new_para()
            WizardIO.out('What AWS region will you use?', indent=2, bold=True)
            WizardIO.out('Supported regions are:', indent=2)
            region_list = AWSConfig.get_supported_regions()
            region_header = map(terminalio.boldify, ['Region', 'Region Name'])

            WizardIO.new_para()
            WizardIO.plain_out(tabulate.tabulate(region_list, headers=region_header, tablefmt='plain'))
            results = self._enter_region(config)

            if results['status'] != 'success':
                return self._quit_setup()

            WizardIO.new_para()
            WizardIO.out('Select or create a VPC', indent=2, bold=True)
            WizardIO.out('Clusterous needs an Amazon Virtual Private Cloud (VPC).', indent=2)
            WizardIO.out('Typically, everyone on the same team can use a single VPC', indent=2)
            success = self._enter_or_select_vpc(config)

            if not success:
                return self._quit_setup()

            WizardIO.new_para()
            WizardIO.out('Select or create a Key Pair', indent=2, bold=True)
            WizardIO.out('Clusterous needs an Amazon Key Pair to establish encrypted connections to clusters', indent=2)
            WizardIO.out("It's usually best to use the same Key Pair as your collaborators", indent=2)
            WizardIO.out('Note that Key Pairs are specific to each AWS region', indent=2)
            success = self._enter_or_select_key_pair(config)

            if not success:
                return self._quit_setup()

            WizardIO.new_para()
            WizardIO.out('Select or create a S3 bucket for Docker images', indent=2, bold=True)
            WizardIO.out('In order to store custom built Docker images, Clusterous needs an S3 bucket', indent=2)
            WizardIO.out('An S3 bucket is a file repository on the AWS cloud', indent=2)
            WizardIO.out('Typically, a team of Clusterous users can share one bucket so that they can use the same Docker images', indent=2)
            success = self._enter_or_select_bucket(config)

            if not success:
                return self._quit_setup()

            WizardIO.new_para()
            WizardIO.out('Enter a name for this configuration profile', indent=2, bold=True)
            WizardIO.out('Give this configuration profile a short but descriptive name', indent=2)
            WizardIO.out('For example "my-project-sydney"', indent=2)
            WizardIO.out('This will make it easy to work with multiple configurations for different regions or accounts', indent=2)
            results = self._enter_profile_name(aws_config)

            if not results['status'] == 'success':
                return self._quit_setup() 

            aws_config.add_profile(results['value'], config)

            WizardIO.new_para()
            WizardIO.out('{0} is now the current profile'.format(results['value']))
            WizardIO.out('Setup is complete. Configuration written to {0}'.format(clusterousconfig.default_config_file))
            WizardIO.out('You are now ready to start using Clusterous')

        except KeyboardInterrupt as e:
            return self._quit_setup()

    @_retry_input
    def _enter_aws_keys(self, config):
        access_key_id = WizardIO.ask('AWS Access Key ID:')
        secret_access_key = WizardIO.ask('AWS Secret Access Key:')

        WizardIO.out('Verifying keys...')
        valid, message = AWSConfig.validate_access_keys(access_key_id, secret_access_key)

        retval = {'status': 'fail', 'message': '', 'value': ''}
        if not valid:
            WizardIO.out(message)
            retval['status'] = 'fail'
            retval['message'] = 'Reenter access keys'
        else:
            config['access_key_id'] = access_key_id
            config['secret_access_key'] = secret_access_key
            retval['status'] = 'success'

        return retval

    @_retry_input
    def _enter_region(self, config):
        region = WizardIO.ask('Region name (e.g. "ap-southeast-2"):')

        retval = {'status': 'fail', 'message': '', 'value': ''}
        region_list = AWSConfig.get_supported_regions()
        if not region in [r[0] for r in region_list]:
            retval['status'] = 'fail'
            retval['message'] = 'Reenter region'
            WizardIO.out('"{}" is not a valid region'.format(region))
        else:
            retval['status'] = 'success'
            config['region'] = region

        return retval

    # No retries
    def _enter_or_select_vpc(self, c):
        vpc_list = AWSConfig.get_available_vpcs(c['access_key_id'], c['secret_access_key'],
                                                c['region'])

        id_obtained = False
        if not vpc_list:
            WizardIO.out('There are currently no available VPCs in this region', indent=2)
            success = self._enter_new_vpc(c)
            if not success:
                WizardIO.out('VPC creation failed: create one manually or contact your administrator', error=True)
            else:
                id_obtained = True
        else:   # vpc_list has nonzero elements

            done = False

            while not done:
                results = self._ask_create_or_select('VPC')
                if results['value'] == 'e':
                    WizardIO.new_para()
                    WizardIO.out('There are {0} available VPCs on your account in this region'.format(len(vpc_list)), indent=2)
                
                    # Tabulate list
                    vpc_headers = map(terminalio.boldify, ['VPC ID', 'VPC Name'])
                    table = tabulate.tabulate(vpc_list, headers=vpc_headers, tablefmt='plain')

                    WizardIO.new_para()
                    WizardIO.plain_out(table)

                    WizardIO.new_para()
                    results = self._enter_existing_vpc_id(c, vpc_list)
                    if results['status'] == 'fail':
                        WizardIO.out('Unable to select VPC')
                        done = True
                        id_obtained = True
                    elif results['status'] == 'cancel':
                        done = False      # Try again
                    elif results['status'] == 'success':
                        done = True
                        id_obtained = True
                    else:
                        done = True
                elif results['value'] == 'n':
                    success = self._enter_new_vpc(c)
                    if not success:
                        WizardIO.out('VPC creation failed: create one manually or contact your administrator', error=True)
                    else:
                        id_obtained = True
                    done = True
                else:
                    return False    # bad selection

        return id_obtained
        

    # No retries
    def _enter_new_vpc(self, c):
        WizardIO.out('Enter a name for a new VPC (e.g. "myproject-cluster")')
        vpc_name = WizardIO.ask('Enter VPC name:')
        WizardIO.out('Creating VPC...')

        valid, message, vpc_id = AWSConfig.create_new_vpc(c['access_key_id'], c['secret_access_key'],
                                                          c['region'], vpc_name)

        if not valid:
            WizardIO.out(message, error=True)
            return False
        else:
            c['vpc_id'] = vpc_id
            WizardIO.out('VPC created')
            return True

    @_retry_input
    def _enter_existing_vpc_id(self, c, vpc_list):
        vpc_id = WizardIO.ask('Enter ID of existing VPC (in the form vpc-xxxx):')

        retval = {'status': 'success', 'message': '', 'value': ''}
        if not vpc_id:
            retval['status'] = 'cancel'
        elif vpc_id not in [ v[0] for v in vpc_list ]:
            retval['status'] = 'fail'
            retval['message'] = 'Selected VPC does not match any on list'
        else:
            c['vpc_id'] = vpc_id

        return retval


    # No retries
    def _enter_or_select_key_pair(self, c):
        key_pair_list = AWSConfig.get_all_key_pairs(c['access_key_id'], c['secret_access_key'],
                                                    c['region'])
        
        key_pair_obtained = False
        if not key_pair_list:
            WizardIO.out('There are currently no Key Pairs in this region', indent=2)
            success = self._enter_new_key_pair(c)
            if not success:
                WizardIO.out('Key Pair creation failed: create one manually or contact your administrator', error=True)
            else:
                key_pair_obtained = True
                WizardIO.out('Key Pair created')
        else:
            done = False

            while not done:
                results = self._ask_create_or_select('Key Pair')
                if results['value'] == 'e':
                    WizardIO.new_para()
                    WizardIO.out('The following are the Key Pairs in this region'.format(len(key_pair_list)), indent=2)

                    WizardIO.new_para()
                    WizardIO.plain_out('\n'.join(key_pair_list))

                    WizardIO.new_para()

                    kp_results = self._enter_existing_key_pair(c, key_pair_list)
                    if kp_results['status'] == 'fail':
                        WizardIO.out('Unable to select Key Pair')
                        done = True
                        key_pair_obtained = True
                    elif kp_results['status'] == 'cancel':
                        done =False     # Try again
                    elif kp_results['status'] == 'success':
                        done = True
                        key_pair_obtained = True
                    else:
                        done = True
                elif results['value'] == 'n':
                    success = self._enter_new_key_pair(c)
                    if not success:
                        WizardIO.out('Key Pair creation failed: create one manually or contact your administrator', error=True)
                    else:
                        key_pair_obtained = True
                        WizardIO.out('Key Pair created')
                    done = True
                else:
                    return False        # bad selection

        return key_pair_obtained

    # No retries
    def _enter_new_key_pair(self, c):
        WizardIO.out('Enter a name for a new Key Pair (e.g. "myproject-cluster")')
        key_pair_name = WizardIO.ask('Enter Key Pair name:')
        WizardIO.out("Enter directory to save the key file. If it doesn't exist, it will be created")
        key_pair_dir = WizardIO.ask('Enter directory (e.g. ~/mykeys):')
        WizardIO.out('Creating Key Pair...')

        success, message = AWSConfig.prepare_key_pair_dir(key_pair_name, key_pair_dir)

        if not success:
            WizardIO.out(message, error=True)
            return False

        success, message, full_path = AWSConfig.create_key_pair(c['access_key_id'], c['secret_access_key'],
                                                    c['region'], key_pair_name, key_pair_dir)
        if not success:
            WizardIO.out(message, error=True)
            return False
        else:
            c['key_pair'] = key_pair_name
            c['key_file'] = full_path

        return True            


    @_retry_input
    def _enter_existing_key_pair(self, c, key_pair_list):
        key_pair_name = WizardIO.ask('Enter name of an existing Key Pair:')
        WizardIO.out("Enter location of your key file (e.g. ~/sshkeys/myproject-cluster.pem)")
        key_pair_file = WizardIO.ask('Enter key file location:')

        retval = {'status': 'fail', 'message': '', 'value': ''}
        if not key_pair_name or not key_pair_file:
            # If user enters blank for any field, treat it as a cancellation
            retval['status'] = 'cancel'
            return retval

        file_valid, message = AWSConfig.validate_key_pair_file(key_pair_file)
        if key_pair_name not in key_pair_list:
            retval['message'] = 'Selected Key Pair does not match any on list'
        elif not file_valid:
            retval['message'] = message
        else:
            retval['status'] = 'success'
            c['key_pair'] = key_pair_name
            c['key_file'] = key_pair_file

        return retval


    # No retries
    def _enter_or_select_bucket(self, c):
        bucket_list = AWSConfig.get_all_buckets(c['access_key_id'], c['secret_access_key'])

        bucket_obtained = False
        if not bucket_list:      # no buckets on account
            success = self._enter_new_bucket()
            if not success:
                WizardIO.out('S3 bucket creation failed: create one manually or contact your administrator', error=True)
            else:
                WizardIO.out('S3 Bucket created')
                bucket_obtained = True
        else:
            done = False

            while not done:
                results = self._ask_create_or_select('S3 bucket')
                if results['value'] == 'e':
                    WizardIO.new_para()
                    WizardIO.out('The following are the S3 buckets on your account'.format(len(bucket_list)), indent=2)

                    WizardIO.new_para()
                    WizardIO.plain_out('\n'.join(bucket_list))

                    WizardIO.new_para()

                    s3_results = self._enter_existing_bucket(c)
                    if s3_results['status'] == 'fail':
                        WizardIO.out('Unable to select S3 bucket')
                        done = True
                        bucket_obtained = True
                    elif s3_results['status'] == 'cancel':
                        done =False     # Try again
                    elif s3_results['status'] == 'success':
                        done = True
                        bucket_obtained = True
                    else:
                        done = True
                elif results['value'] == 'n':
                    success = self._enter_new_bucket(c)
                    if not success:
                        WizardIO.out('S3 bucket creation failed: create one manually or contact your administrator', error=True)
                    else:
                        WizardIO.out('S3 Bucket created')
                        bucket_obtained = True
                    done = True
                else:
                    return False        # bad selection                    

        return bucket_obtained

    # No retries
    def _enter_new_bucket(self, c):
        WizardIO.out("Enter a name for a new S3 bucket. Note that bucket names aren't specfic to a region")
        WizardIO.out("In fact, bucket names are global across Amazon, so it's best to give it a well qualified name")
        WizardIO.out('e.g. "myorg-myproject-clusterous". The bucket contents will be private')
        bucket_name = WizardIO.ask('Enter an S3 bucket name:')

        success, message = AWSConfig.create_s3_bucket(c['access_key_id'], c['secret_access_key'], c['region'], bucket_name)

        if not success:
            WizardIO.out(message, error=True)
            return False
        else:
            c['clusterous_s3_bucket'] = bucket_name

        return True

    @_retry_input
    def _enter_existing_bucket(self, c):
        bucket_name = WizardIO.ask('Enter name of an existing S3 bucket:')

        retval = {'status': 'fail', 'message': '', 'value': ''}
        if not bucket_name:
            retval['status'] = 'cancel'
            return retval

        valid, message = AWSConfig.validate_s3_bucket(c['access_key_id'], c['secret_access_key'], bucket_name)
        if not valid:
            retval['message'] = message
        else:
            retval['status'] = 'success'
            c['clusterous_s3_bucket'] = bucket_name

        return retval

    @_retry_input
    def _enter_profile_name(self, aws_config):
        profile_name = WizardIO.ask('Enter a profile name:')

        # Ensure that profile name isn't in use, and is valid
        valid = not aws_config.is_profile_name_in_use(profile_name)
        
        retval = {'status': 'fail', 'message': '', 'value': ''}
        if not valid:
            retval['status'] = 'fail'
            retval['message'] = 'Profile name is not valid. It may already be in use'
        else:
            retval['status'] = 'success'
            retval['value'] = profile_name

        return retval

    @_retry_input
    def _ask_create_or_select(self, resource_str):
        WizardIO.out('Do you want to select an (e)xisting {0} or create a (n)ew one?'.format(resource_str))
        selection = WizardIO.ask("Enter either 'e' or 'n':").lower()

        retval = {'status': 'fail', 'message': '', 'value': ''}
        if not selection in ('e', 'n'):
            retval['status'] = 'fail'
            retval['message'] = "Enter either 'e' or 'n'"
        else:
            retval['status'] = 'success'
            retval['value'] = selection

        return retval

