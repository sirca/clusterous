import logging
import yaml
import os.path

class ParseError(Exception):
    def __init__(self, msg, parents=[]):
        self.msg = msg
        self.parents = parents

    def __str__(self):
        p = ''
        if self.parents:
            p = 'In {0}'.format(' > '.join(self.parents))

        return '{0}: {1}'.format(p, self.msg)

class UnknownValue(Exception):
    """
    For use when unknown "$" value found in environment file.
    Usually means user hasn't supplied the value in the profile file.
    """
    pass

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

    def __init__(self, env_file, params={}):
        self._logger = logging.getLogger(__name__)
        self._env_filename = env_file
        yaml_data = self._read_yaml(self._env_filename)

        # Get base path
        abspath = os.path.abspath(self._env_filename)
        self.base_path = os.path.dirname(abspath)

        self.spec = self._parse_environment_file(yaml_data, params)

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

    def _parse_environment_file(self, data, params):
        parsed = {}
        try:
            if not 'name' in data:
                raise ParseError('Expected "name" section')
            parsed['name'] = data['name']

            parsed['environment'] = {}
            parsed['cluster'] = {}
            if 'environment' in data:
                parsed['environment'] = self._parse_environment_section(data['environment'])

            if 'cluster' in data:
                parsed['cluster'] = self._parse_cluster_section(data['cluster'], params)

        except ParseError as e:
            self._logger.error(e)
        except UnknownValue as e:
            self._logger.error('Expected value "{0}" not present'.format(e))

        return parsed

    def _parse_environment_section(self, env):
        # Validate environment section
        component_schema = {
                            'machine': (True,),
                            'cpu': (True,),
                            'image': (True,),
                            'cmd': (True,),
                            'attach_volume': (False, 'yes'),
                            'ports': (False, ''),
                            'count': (False, 1),
                            'depends': (False, '')
                            }
        validator = DictValidator(component_schema)
        new_env = {}
        new_env['components'] = {}
        for component, fields in env['components'].iteritems():
            validated_fields = validator.validate(fields)
            new_env['components'][component] = validated_fields

        new_env['image'] = env['image']
        new_env['copy'] = env['copy']
        new_env['expose_tunnel'] = env['expose_tunnel']
        return new_env

    def _parse_cluster_section(self, cluster, params):
        new_cluster = {}
        for machine, fields in cluster.iteritems():
            if (len(fields) != 2 and
                ('count' in fields and 'type' in fields)):
                raise ParseError('Invalid values for machine "{0}"'.format(machine))
            new_cluster[machine] = {}
            for field_name, field_val in fields.iteritems():
                val = self._process_field_value(field_val, params)
                new_cluster[machine][field_name] = val

        return new_cluster

    def _process_field_value(self, field, params):
        """
        Given a value, substitute any user-supplied '$' variables.
        E.g. "$num_nodes" gets converted to "3" if params has num_nodes=3
        Supports "-1" syntax
        Returns numerical value for field
        """
        tokens = []
        # If the field is a string value
        if isinstance(field, str):
            if '-' in field:
                tokens = field.split('-')
                if len(tokens) != 2:
                    raise ParseError('Invalid syntax: "{0}"'.format(field))
                left = tokens[0].strip()
                if left.startswith('$'):
                    var = left[1:]
                else:
                    raise ParseError('Unrecognised string in "{0}"'.format(field))
                # $var does not match any supplied in params, this is a special error
                if not var in params:
                    raise UnknownValue(var)
                var_val = params[var]
                if not isinstance(var_val, int):
                    raise ParseError('Expected integer value for "{0}"'.format(var))

                # Ensure right hand argument is also an int
                right = tokens[1].strip()
                if not right.isdigit():
                    raise ParseError('Right hand value must be integer: "{0}"'.format(field))

                value = var_val - int(right)
            else:
                stripped = field.strip()
                if stripped.startswith('$'):
                    var = stripped[1:]
                else:
                    raise ParseError('Unrecognised value: "{0}"'.format(field))
                if not var in params:
                    raise UnknownValue(var)
                value = params[var]

        elif isinstance(field, int):
            # Field is a simple integer
            value = field
        else:
            raise ParseError('Unknown field value type: "{0}"'.format(field))

        return value
