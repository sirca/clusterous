# Configuration file for iplogger.

c = get_config()

#------------------------------------------------------------------------------
# IPLoggerApp configuration
#------------------------------------------------------------------------------

# IPLoggerApp will inherit config from: BaseParallelApplication,
# BaseIPythonApplication, Application

# The IPython profile to use.
# c.IPLoggerApp.profile = u'default'

# Set the log level by value or name.
# c.IPLoggerApp.log_level = 30

# Set the working dir for the process.
# c.IPLoggerApp.work_dir = u'/home/data/setup'

# whether to log to a file
# c.IPLoggerApp.log_to_file = False

# The ZMQ URL of the iplogger to aggregate logging.
# c.IPLoggerApp.log_url = ''

# Path to an extra config file to load.
# 
# If specified, load this config file in addition to any other IPython config.
# c.IPLoggerApp.extra_config_file = u''

# Whether to create profile dir if it doesn't exist
# c.IPLoggerApp.auto_create = False

# whether to cleanup old logfiles before starting
# c.IPLoggerApp.clean_logs = False

# String id to add to runtime files, to prevent name collisions when using
# multiple clusters with a single profile simultaneously.
# 
# When set, files will be named like: 'ipcontroller-<cluster_id>-engine.json'
# 
# Since this is text inserted into filenames, typical recommendations apply:
# Simple character strings are ideal, and spaces are not recommended (but should
# generally work).
# c.IPLoggerApp.cluster_id = ''

# Whether to install the default config files into the profile dir. If a new
# profile is being created, and IPython contains config files for that profile,
# then they will be staged into the new directory.  Otherwise, default config
# files will be automatically generated.
# c.IPLoggerApp.copy_config_files = False

# The date format used by logging formatters for %(asctime)s
# c.IPLoggerApp.log_datefmt = '%Y-%m-%d %H:%M:%S'

# The Logging format template
# c.IPLoggerApp.log_format = '[%(name)s]%(highlevel)s %(message)s'

# Create a massive crash report when IPython encounters what may be an internal
# error.  The default is to append a short message to the usual traceback
# c.IPLoggerApp.verbose_crash = False

# The name of the IPython directory. This directory is used for logging
# configuration (through profiles), history storage, etc. The default is usually
# $HOME/.ipython. This option can also be specified through the environment
# variable IPYTHONDIR.
# c.IPLoggerApp.ipython_dir = u''

# Whether to overwrite existing config files when copying
# c.IPLoggerApp.overwrite = False

#------------------------------------------------------------------------------
# LogWatcher configuration
#------------------------------------------------------------------------------

# A simple class that receives messages on a SUB socket, as published by
# subclasses of `zmq.log.handlers.PUBHandler`, and logs them itself.
# 
# This can subscribe to multiple topics, but defaults to all topics.

# ZMQ url on which to listen for log messages
# c.LogWatcher.url = u''

# The ZMQ topics to subscribe to. Default is to subscribe to all messages
# c.LogWatcher.topics = ['']

#------------------------------------------------------------------------------
# ProfileDir configuration
#------------------------------------------------------------------------------

# An object to manage the profile directory and its resources.
# 
# The profile directory is used by all IPython applications, to manage
# configuration, logging and security.
# 
# This object knows how to find, create and manage these directories. This
# should be used by any code that wants to handle profiles.

# Set the profile location directly. This overrides the logic used by the
# `profile` option.
# c.ProfileDir.location = u''
