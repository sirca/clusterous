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

import logging
import yaml
import os.path

import helpers
from helpers import SchemaEntry
import defaults

class EnvironmentSpecError(Exception):
    pass

class ParseError(EnvironmentSpecError):
    pass

class UnknownValue(EnvironmentSpecError):
    """
    For use when unknown "$" value found in environment file.
    Usually means user hasn't supplied the value in the profile file.
    """
    def __str__(self):
        return 'The following parameter was expected but not supplied: "{0}"'.format(self.message)

class UnknownParams(EnvironmentSpecError):
    """
    For use if the params have extra variables that are not used in this environent file.
    This can suggest a user error.
    """
    def __init__(self, unknown_params=[]):
        super(UnknownParams, self).__init__('')
        self.unknown_params = unknown_params

    def __str__(self):
        plural_str = 'parameter was'
        if len(self.unknown_params) > 1:
            plural_str = 'parameters were'
        unknowns_str = ', '.join(self.unknown_params)
        return 'The following {0} supplied but not recognised: {1}'.format(plural_str, unknowns_str)

class DictValidator(object):
    # TODO: helpers.validate could potentiall replace this, if it supports
    # arbitrary fields (like under the components section)
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

    def __init__(self, env_file, params={}, profile_file_path=None):
        self._logger = logging.getLogger(__name__)

        # Obtain actual path of environment file (which may be relative to profile_file_path)
        if profile_file_path:
            profile_base = os.path.dirname(os.path.abspath(os.path.expanduser(profile_file_path)))
            self._env_filename = os.path.join(profile_base, env_file)
        else:
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

        if not os.path.isfile(environment_file):
            raise EnvironmentSpecError('Cannot open file')

        stream = open(environment_file, 'r')

        try:
            contents = yaml.load(stream)
        except yaml.YAMLError as e:
            raise EnvironmentSpecError('Invalid YAML format: ' + str(e))

        stream.close()
        return contents

    def _parse_environment_file(self, data, params):
        parsed = {}
        tunnel_schema = {
                    'service': SchemaEntry(True, '', str, None),
                    'message': SchemaEntry(False, '', str, None)
        }
        env_schema = {
                    'copy': SchemaEntry(False, [], list, None),
                    'image': SchemaEntry(False, [], list, None),
                    'components': SchemaEntry(True, {}, dict, None),
                    # TODO: enhance validation such that expose_tunnel can be validated here
                    'expose_tunnel': SchemaEntry(False, {}, None, None)
        }
        top_schema = {
                    'name': SchemaEntry(True, '', str, None),
                    'environment': SchemaEntry(False, {}, dict, env_schema),
                    'cluster': SchemaEntry(False, {}, dict, None)
        }

        is_valid, message, validated = helpers.validate(data, top_schema)

        if not is_valid:
            raise ParseError(message)

        if not defaults.taggable_name_re.match(validated['name']):
            raise ParseError('Invalid characters in name')

        # Validate expose_tunnel separately (because it can be either a dictionary or a list)
        if 'environment' in top_schema and 'expose_tunnel' in top_schema['environment']:
            expose_tunnel = top_schema['environment']['expose_tunnel']
            if type(expose_tunnel) == dict:
                tunnel_valid, tunnel_msg, tunnel_validated = helpers.validate(expose_tunnel, tunnel_schema)
            elif type(expose_tunnel) == list:
                for e in expose_tunnel:
                    tunnel_valid, tunnel_msg, tunnel_validated = helpers.validate(expose_tunnel, tunnel_schema)
                    if not tunnel_valid:
                        break
            else:
                raise ParseError('expose_tunnel must be either a list or dictionary')
            if not tunnel_valid:
                raise ParseError(tunnel_msg)

        if 'components' in validated.get('environment', {}):
            validated['environment']['components'] = self._parse_components_section(validated['environment']['components'])

        if 'cluster' in validated:
            validated['cluster'] = self._parse_cluster_section(validated['cluster'], params)

        return validated

    def _parse_components_section(self, comps):
        # Validate environment section using DictValidator
        component_schema = {
                            'machine': (True,),
                            'cpu': (True,),
                            'image': (True,),
                            'cmd': (True,),
                            'attach_volume': (False, True),
                            'ports': (False, ''),
                            'count': (False, 1),
                            'depends': (False, '')
                            }
        validator = DictValidator(component_schema)
        new_comps = {}
        for component, fields in comps.iteritems():
            validated_fields = validator.validate(fields)
            if (validated_fields['cpu'] != 'auto' and
                    not type(validated_fields['cpu']) in (int, float)):
                raise ParseError('In "{0}", invalid value for "cpu": {1}'.format(component, type(validated_fields['cpu'])))
            if (isinstance(validated_fields['cpu'], (int, float)) and
                not validated_fields['cpu'] > 0):
                raise ParseError('In "{0}", "cpu" must be positive'.format(component))
            if validated_fields['attach_volume'] not in (True, False):
                raise ParseError('In "{0}", "attach_volume" must be a boolean yes/no value'.format(component))
            new_comps[component] = validated_fields

        return new_comps

    def _parse_cluster_section(self, cluster, params):
        new_cluster = {}
        substituted_vars = []
        for machine, fields in cluster.iteritems():
            if (len(fields) != 2 and
                ('count' in fields and 'type' in fields)):
                raise ParseError('Invalid values for machine "{0}"'.format(machine))
            new_cluster[machine] = {}
            for field_name, field_val in fields.iteritems():
                val, substituted, substituted_var = self._process_field_value(field_val, params)
                if substituted:
                    substituted_vars.append(substituted_var)
                new_cluster[machine][field_name] = val
                if field_name == 'count' and substituted:
                    new_cluster[machine]['scalable'] = True


        # Check if params has any fields not substituted (possible user error)
        if set(substituted_vars) != set(params.keys()):
            unknowns = list(set(params.keys()) - set(substituted_vars))
            raise UnknownParams(unknowns)

        return new_cluster

    def _process_field_value(self, field, params):
        """
        Given a value, substitute any user-supplied '$' variables.
        E.g. "$num_nodes" gets converted to "3" if params has num_nodes=3
        Supports "-1" syntax
        Returns value for field
        """
        tokens = []
        substituted = True
        substituted_var = ''
        # If the field is a string value
        if isinstance(field, str):
            if '-' in field:
                tokens = field.split('-')
                if len(tokens) != 2:
                    raise ParseError('Invalid syntax: "{0}"'.format(field))
                left = tokens[0].strip()
                if left.startswith('$'):
                    var = left[1:]
                    substituted_var = var
                else:
                    raise ParseError('Unrecognised string in "{0}"'.format(field))
                # $var does not match any supplied in params, this is a special error
                if not var in params:
                    raise UnknownValue(var)
                var_val = params[var]
                if not isinstance(var_val, int):
                    raise ParseError('Expected integer value for "{0}"'.format(var))
                if var_val <= 0:
                    raise ParseError('Expected positive value for "{0}"'.format(var))

                # Ensure right hand argument is also an int
                right = tokens[1].strip()
                if not right.isdigit():
                    raise ParseError('Right hand value must be integer: "{0}"'.format(field))

                value = var_val - int(right)
            else:
                stripped = field.strip()
                if stripped.startswith('$'):
                    var = stripped[1:]
                    substituted_var = var
                else:
                    raise ParseError('Unrecognised value: "{0}"'.format(field))
                if not var in params:
                    raise UnknownValue(var)
                value = params[var]

        elif isinstance(field, int):
            # Field is a simple integer
            value = field
            substituted = False
        else:
            raise ParseError('Unknown field value type: "{0}"'.format(field))

        return value, substituted, substituted_var
