import boto3, botocore
import os
import time

default_config_file = '~/.clusterous.yml'

class ConfigError(Exception):
    pass

class ClusterousConfig:
    def _read_config(self, filename):
        try:
            stream = open(os.path.expanduser(config_file), 'r')
            contents = yaml.load(stream)
            stream.close()
        except IOError as e:
            raise ConfigError(str(e), config_file)
        except yaml.YAMLError as e:
            raise ConfigError('Invalid YAML format: ' + str(e), config_file)


    def __init__(self, config_file=''):  
        if config_file:
            filename = os.path.expanduser(config_file)
        else:
            filename = os.path.expanduser(default_config_file)

        config = _read_config(self, filename)

class AWSConfig(ClusterousConfig):

    supported_regions = [
        'us-west-1', 'us-west-2', 'us-east-1',
        'eu-west-1', 'eu-central-1', 'ap-northeast-1',
        'ap-southeast-1', 'ap-southeast-2', 'sa-east-1'
   ]    

    # def __init__(self, config_file=''):
    #     super(AWSConfig, self).__init__(config_file)



    @staticmethod
    def validate_access_keys(access_key_id, secret_access_key):
        # Perform a test connection with ec2 in ap-southeast-2 to check if keys are valid
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                        region_name='ap-southeast-2')

        client = session.client('ec2')
        try:
            regions = client.describe_regions()
        except botocore.exceptions.ClientError as e:
            return False, 'Provided access key id or secret access key could not be authenticated'
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

        full_name = None
        # Save key file
        try:
            file_name = key_pair_name + '.pem'
            full_name = os.path.join(os.path.expanduser(dirname), file_name)
            f = open(full_name, 'w')
            f.write(kp['KeyMaterial'])
            f.close()
            # Set appropriate permissions
            os.chmod(full_name, 0600)
        except (IOError, OSError) as e:
            return False, 'Error writing key to file {0}'.format(full_name), None

        return True, '', full_name

    @staticmethod
    def validate_key_pair_file(key_pair_file):
        expanded = os.path.expanduser(key_pair_file)
        if not os.path.isfile(expanded):
            return False, 'Cannot locate key file "{0}"'.format(key_pair_file)

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
    def create_s3_bucket(access_key_id, secret_access_key, region, bucket_name):
        session = boto3.session.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
        client = session.client('s3')

        try:
            resp = client.create_bucket(ACL='private', Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                return False, 'Bucket "(0}" already exists. Note that bucket namespace is shared by all AWS users'.format(bucket_name)
            else:
                return False, 'Error creating bucket'

        return True, 

    @staticmethod
    def validate_s3_bucket(access_key_id, secret_access_key, bucket_name):
        """
        Check if user has adequate permissions to use bucket
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
