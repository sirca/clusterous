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

import boto3, botocore

import os
import stat
import time
import yaml

default_config_file = '~/.clusterous.yml'

class ConfigError(Exception):
    pass

class OldConfigError(ConfigError):
    pass

class ClusterousConfig:

    default_contents = {'current_profile': '', 'profiles': {}}

    def __init__(self, config_file=''):  
        if config_file:
            self._config_file = os.path.expanduser(config_file)
        else:
            self._config_file = os.path.expanduser(default_config_file)

        self._config = self._read_config(self._config_file)


    def _read_config(self, filename):
        contents = {}

        if os.path.isfile(os.path.expanduser(filename)):
            try:
                stream = open(os.path.expanduser(filename), 'rw')
                contents = yaml.load(stream)
                stream.close()
                if not contents:
                    # If file is blank, create and populate with blank fields
                    contents = ClusterousConfig.default_contents
                else:
                    # Validate basic fields
                    if not 'current_profile' in contents or not 'profiles' in contents:
                        if type(contents) == list and len(contents) > 0 and 'AWS' in contents[0]:
                            raise OldConfigError('Invalid format, configuration may be in an older format')
                        else:
                            raise ConfigError('Invalid format, expected "current_profile" and "profiles" section: ' + filename)
            except IOError as e:
                raise ConfigError(str(e))
            except yaml.YAMLError as e:
                raise ConfigError('Invalid YAML format: ' + str(e))
        else:
            # File doesn't exist, just fill default value
            contents = ClusterousConfig.default_contents


        return contents


    def _write_config(self):
        """
        Write to config file
        """
        comment = '# Generated by Clusterous on {0}\n'.format(time.ctime())

        stream = open(self._config_file, 'w')
        stream.write(comment)
        yaml.dump(self._config, stream, default_flow_style=False)
        stream.close()

        return True

    def _get_cloud_type(self):
        return 'null'


    def get_current_profile_name(self):
        return self._config.get('current_profile', '')

    def get_current_profile(self):
        current_profile_name = self._config.get('current_profile', None)

        if not current_profile_name:
            return None

        # TODO: raise exception if missing
        return self._config['profiles'].get(current_profile_name, {}).get('config', {})

    def get_current_profile_type(self):
        current_profile_name = self._config.get('current_profile', None)

        if not current_profile_name:
            return None

        return self._config['profiles'].get(current_profile_name, {}).get('type', {})

    def get_current_profile_info(self):
        """
        Gets name, config and type of current profile
        """
        name = self.get_current_profile_name()
        config = self.get_current_profile()
        config_type = self.get_current_profile_type()

        return name, config, config_type

    def get_config_for_profile(self, profile_name):
        name = profile_name
        if not profile_name:
            name = self.get_current_profile_name()

        return self._config['profiles'].get(name, {})


    def add_profile(self, profile_name, config):
        if profile_name in self._config['profiles']:
            raise ProfileError('Profile already exists')
        config_type = self._get_cloud_type()
        inner = {'type': config_type, 'config': config}

        self._config['profiles'][profile_name] = inner

        # Set current profile to the new profile
        self._config['current_profile'] = profile_name

        self._write_config()

        return True

    def get_profile_list(self):
        return self._config['profiles'].keys()


    def set_current_profile(self, profile_name):
        if not self.is_profile_name_in_use(profile_name):
            return False, 'No profile matches "{0}"'.format(profile_name)

        if self._config['current_profile'] == profile_name:
            return False, '"{0}" is already the current profile'.format(profile_name)

        self._config['current_profile'] = profile_name

        self._write_config()
        return True, ''

    def delete_profile(self, profile_name):
        if not self.is_profile_name_in_use(profile_name):
            return False, 'No profile matches "{0}"'.format(profile_name)

        if profile_name == self.get_current_profile_info():
            return False, 'Cannot delete currently active profile'

        del self._config['profiles'][profile_name]

        self._write_config()
        return True, ''        

    def is_profile_name_in_use(self, profile_name):
        # TODO: check for characters etc
        if 'profiles' in self._config and self._config['profiles']:
            if profile_name in self._config['profiles'].keys():
                return True
        
        return False


class AWSConfig(ClusterousConfig):

    supported_regions = [
        ['us-west-1', 'US West (N. California)'],
        ['us-west-2', 'US West (Oregon)'],
        ['us-east-1', 'US East (N. Virginia)'],
        ['eu-west-1', 'EU (Ireland)'],
        ['eu-central-1', 'EU (Frankfurt)'],
        ['ap-northeast-1', 'Asia Pacific (Tokyo)'],
        ['ap-southeast-1', 'Asia Pacific (Singapore)'],
        ['ap-southeast-2', 'Asia Pacific (Sydney)'],
        ['sa-east-1', 'South America (Sao Paulo)']
   ]    


    def _get_cloud_type(self):
        """
        Override from super class
        """
        return 'AWS'

    @staticmethod
    def validate_access_keys(access_key_id, secret_access_key):
        # Perform a test connection with ec2 in ap-southeast-2 to check if keys are valid
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                        region_name='ap-southeast-2')

        client = session.client('ec2')
        try:
            regions = client.describe_regions()
        except botocore.exceptions.ClientError as e:
            return False, 'Access key id or secret access key could not be authenticated'
        except botocore.exceptions.EndpointConnectionError as e:
            return False, 'Could not connect to AWS'

        return True, ''

    @staticmethod
    def get_supported_regions():
        return AWSConfig.supported_regions

    @staticmethod
    def get_available_vpcs(access_key_id, secret_access_key, region):
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                        region_name=region)
        client = session.client('ec2')

        vpc_list = []
        try:
            vpcs = client.describe_vpcs()
            for v in vpcs.get('Vpcs', []):
                if v['State'] == 'available':
                    name = ''
                    for tag in v.get('Tags', []):
                        if tag.get('Key', '') == 'Name':
                            name = tag.get('Value', '')
                    l = [v['VpcId'], name]
                    vpc_list.append(l)

        except botocore.exceptions.ClientError as e:
            return False, 'Provided access key id or secret access key could not be authenticated'
        except botocore.exceptions.EndpointConnectionError as e:
            return False, 'Could not connect to AWS'

        return vpc_list

    @staticmethod
    def create_new_vpc(access_key_id, secret_access_key, region, vpc_name):
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                        region_name=region)
        client = session.client('ec2')

        vpc_id = ''
        tags = [{'Key': 'Name', 'Value': vpc_name}, {'Key': 'Clusterous', 'Value': ''}]
        try:
            # Create VPC and wait till available
            res = client.create_vpc(CidrBlock='10.144.0.0/16')
            vpc_id = res['Vpc']['VpcId']
            max_tries = 10
            count = 0
            available = False
            while not available and count < max_tries:
                count +=1
                state = client.describe_vpcs(VpcIds=[vpc_id])
                available = True if state['Vpcs'][0]['State'] == 'available' else False
                if not available:
                    time.sleep(2)
            # VPC should now be available
            client.create_tags(Resources=[vpc_id], Tags=tags)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'VpcLimitExceeded':
                return False, 'VPC quota has been reached, cannot create a new one', ''
            else:
                return False, 'Error creating VPC'
        except botocore.exceptions.EndpointConnectionError as e:
            return False, 'Could not connect to AWS'

        if vpc_id:
            return True, None, vpc_id
        else:
            return False, 'Unknown error', ''

    @staticmethod
    def get_all_key_pairs(access_key_id, secret_access_key, region):
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                        region_name=region)
        client = session.client('ec2')

        key_pair_list = []
        try:        
            pairs = client.describe_key_pairs()
            for p in pairs.get('KeyPairs', []):
                if 'KeyName' in p:
                    key_pair_list.append(p['KeyName'])

        except botocore.exceptions.ClientError as e:
            return False, 'Provided access key id or secret access key could not be authenticated'

        return key_pair_list

    @staticmethod
    def prepare_key_pair_dir(key_pair_name, dirname):
        full_path = os.path.expanduser(dirname)
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return False, '{0} must be a directory, not a file'.format(dirname)

        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path, mode=0744)
            except OSError as e:
                return False, 'Unable to create directory: {0}'.format(e)
        else:
            if not os.access(full_path, os.W_OK):
                return False, 'Do not have write permissions for directory {0}'.format(dirname)

        return True, ''

    @staticmethod
    def create_key_pair(access_key_id, secret_access_key, region, key_pair_name, dirname):
        # Get refreshed list of existing keypairs
        existing = AWSConfig.get_all_key_pairs(access_key_id, secret_access_key, region)

        if key_pair_name in existing:
            return False, 'A Key Pair with name "{0}" already exists'.format(key_pair_name), None

        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                        region_name=region)
        client = session.client('ec2')        

        try:
            kp = client.create_key_pair(KeyName=key_pair_name)
        except botocore.exceptions.ClientError as e:
            return False, 'Error creating Key Pair', None

        user_file_path = ''     # file path without '~' expanded
        # Save key file
        try:
            file_name = key_pair_name + '.pem'
            full_name = os.path.join(os.path.expanduser(dirname), file_name)
            user_file_path = os.path.join(dirname, file_name)
            f = open(full_name, 'w')
            f.write(kp['KeyMaterial'])
            f.close()
            # Set appropriate permissions
            os.chmod(full_name, 0600)
        except (IOError, OSError) as e:
            return False, 'Error writing key to file {0}'.format(user_file_path), None

        return True, '', user_file_path

    @staticmethod
    def validate_key_pair_file(key_pair_file):
        expanded = os.path.expanduser(key_pair_file)
        if not os.path.isfile(expanded):
            return False, 'Cannot locate key file "{0}"'.format(key_pair_file)

        # Set appropriate permissions
        if oct(stat.S_IMODE(os.stat(expanded).st_mode)) != '0600':
            try:
                os.chmod(expanded, 0600)
            except OSError as e:
                return False, 'Unable to change permissions for "{0}", permissions must be 600 (not readable by others)'
        return True, ''

    @staticmethod
    def get_all_buckets(access_key_id, secret_access_key):
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)

        client = session.client('s3')

        bucket_list = []
        try:
            raw_list = client.list_buckets()
            for b in raw_list['Buckets']:
                bucket_list.append(b['Name'])

        except botocore.exceptions.ClientError as e:
            return False, 'Provided access key id or secret access key could not be authenticated'
        except botocore.exceptions.EndpointConnectionError as e:
            return False, 'Could not connect to AWS' 

        return bucket_list

    @staticmethod
    def _validate_s3_bucket_name(self, name):
        """
        Validates name of an S3 bucket, ensuring compliance with most of the
        restrictions described by Amazon:
        http://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html
        In addition, Clusterous doesn't allow dots in S3 bucket names to avoid
        SSL issues.

        Returns 2-tuple in the form (success, message)
        """
        s3_re = re.compile('^[a-z0-9][a-z0-9-]+$')

        if '.' in name:
            return False, 'Dots in bucket name not supported'

        if not 3 <= len(name) <= 63:
            return False, 'Must be between 3 and 63 characters long (inclusive)'

        if not s3_re.search(name):
            return False, 'Contains invalid characters'

        return True, ''

    @staticmethod
    def create_s3_bucket(access_key_id, secret_access_key, region, bucket_name):
        success, message = self._validate_s3_bucket_name(bucket_name)

        if not success:
            return False, message

        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
        client = session.client('s3')

        try:
            resp = client.create_bucket(ACL='private', Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                return False, 'Bucket "(0}" already exists. Note that bucket namespace is shared by all AWS users'.format(bucket_name)
            else:
                return False, 'Error creating bucket'

        return True, ''

    @staticmethod
    def validate_s3_bucket(access_key_id, secret_access_key, bucket_name):
        """
        Check if bucket exists and user has adequate permissions to use bucket
        """
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
        client = session.client('s3')
        try:
            client.head_bucket(Bucket=bucket_name)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '403':
                return False, 'Inadequate permissions to use bucket "{0}"'.format(bucket_name)
            else:
                return False, 'Error with bucket "{0}", unable to access'.format(bucket_name)

        return True, ''
