import logging
import yaml
import os.path

class ParseError(Exception):
    def __init__(self, msg, parents=[]):
        self.msg = msg
        self.parents = parents

    def __str__():
        p = ''
        if self.parents:
            p = 'In {0}'.format(' > '.join(self.parents))

        return '{0}: {1}'.format(p, self.msg)

class DictValidator(object):
    """
    Simple class for validating a dictionary.
    Takes a trivial schema that states which keys
    are mandatory, and for optional keys, what
    the default value should be
    """
    def __init__(self, schema={}):
        """
        Schema must be a dictionary, with key representing
        key name, and value as a tuple. First element of tuple
        should be bool representing if the field is mandatory.
        Second element is default value.
        """
        self.schema = schema

    def validate(self, in_dict):
        """
        Runs validation on in_dict, returns a validated dict
        """
        ret = in_dict.copy()
        for key, rules in self.schema.iteritems():
            if rules[0] and key not in ret:
                raise ParseError('Missing mandatory key "{0}"'.format(key))
            elif not rules[0] and key not in ret:
                if rules[1] is not None:
                    ret[key] = rules[1]
                else:
                    ret[key] = None
        return ret

class EnvironmentFile(object):
    """
    Reads and parses an environment file
    """

    def __init__(self, env_file):
        self._logger = logging.getLogger(__name__)
        self._env_filename = env_file
        yaml_data = self._read_yaml(self._env_filename)

        # Get base path
        abspath = os.path.abspath(self._env_filename)
        self.base_path = os.path.dirname(abspath)

        self.spec = self._parse_environment_file(yaml_data)

    def get_full_path(self, rel_path):
        """
        Given a relative path, returns the absolute path relative to the
        environment file's base path
        """
        return os.path.join(self.base_path, rel_path)

    def _read_yaml(self, environment_file):
        """
        Loads environment file into yaml dictionary
        """

        stream = open(environment_file, 'r')
        contents = yaml.load(stream)
        stream.close()
        #TODO handle error
        return contents

    def _parse_environment_file(self, data):
        parsed = {}
        try:
            if len(data.keys()) != 2:
                self._logger.error('Expected 2 sections in {0}, got {1}'.format(self._env_filename, len(data.keys())))
                raise ParseError('Expected 2 sections, got {1}'.format(len(data)))
            if not 'name' in data or not 'environment' in data:
                raise ParseError('Expected "name" and "environment" sections')
            parsed['name'] = data['name']

            # Validate environment section
            component_schema = {
                                'machine': (True,),
                                'cpu': (True,),
                                'image': (True,),
                                'cmd': (True,''),
                                'attach_volume': (False, 'yes'),
                                'ports': (False, ''),
                                'count': (False, 1),
                                'depends': (False, '')
                                }
            validator = DictValidator(component_schema)
            new_env = {}
            new_env['components'] = {}
            for component, fields in data['environment']['components'].iteritems():
                validated_fields = validator.validate(fields)
                new_env['components'][component] = validated_fields

            parsed['environment'] = new_env
            parsed['environment']['image'] = data.get('environment',{}).get('image',{})
            parsed['environment']['copy'] = data.get('environment',{}).get('copy',{})
            parsed['environment']['expose_tunnel'] = data.get('environment',{}).get('expose_tunnel',{})

        except ParseError as e:
            self._logger.error(e)

        return parsed
