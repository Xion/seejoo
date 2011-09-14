'''
Created on 2010-12-05

@author: xion

Configuration module. Contains code for reading the configuration
from command line and/or YAML file.
'''
from optparse import OptionGroup, OptionParser # Not argparse since we target Python 2.6 as well
import logging


###############################################################################
# Config class

class Config(object):
    '''
    Configuration class. Stores bot's settings, read from command line
    and/or YAML configuration file
    '''
    def __init__(self):
        self.set_defaults()
          
    def set_defaults(self):
        '''
        Sets the default configuration settings.
        '''
        # IRC options
        self.nickname = NICKNAME
        self.server = SERVER
        self.port = PORT
        self.channels = CHANNELS
        
        # Command options
        self.cmd_prefix = PUBLIC_PREFIX
        self.commands = COMMANDS
        self.plugins = PLUGINS
        
    def parse_args(self):
        '''
        Loads configuration settings from command line.
        These take precedence before the settings from config file
        (if custom config file is supplied), which in turn take precedence before
        settings from default config file (if present).
        @note: If command line specifies custom config file, it will be loaded
        by this function.
        '''
        # Create option parser and option groups
        op = OptionParser()
        gen_opts = OptionGroup(op, "General options")
        irc_opts = OptionGroup(op, "IRC options", "These options control bot behavior in the IRC network.")
        cmd_opts = OptionGroup(op, "Command options")
        
        # Set options in groups
        gen_opts.add_option("--cfg", "--config", dest = "config_file",
                            help = "FILE (in YAML format) from which the configuration options shall be read",
                            metavar = "FILE")
        irc_opts.add_option("-n", "--nickname", dest = "nickname",
                            help = "NICKNAME which will be used by the bot", metavar = "NICKNAME")
        irc_opts.add_option("-s", "--server", dest = "server",
                            help = "SERVER to which bot shall connect", metavar = "SERVER")
        irc_opts.add_option("-p", "--port", dest = "port", type = "int",
                            help = "Server's PORT to which bot shall connect; usually 6667, which is default",
                            metavar = "PORT")
        irc_opts.add_option("-c", "--chan", "--channel", dest = "channels", action = "append",
                            help = "CHANNEL which the bot shall reside in. This option can be specified multiple times.",
                            metavar = "CHANNEL")
        cmd_opts.add_option("--prefix", dest = "cmd_prefix",
                            help = "PREFIX to be used in public channels before commands; a dot by default",
                            metavar = "PREFIX")
        
        # Add groups to parser
        op.add_option_group(gen_opts)
        op.add_option_group(irc_opts)
        op.add_option_group(cmd_opts)
        
        # Do the parsing and read the specified config file, if supplied
        (options, _) = op.parse_args()
        if options.config_file:
            try:    self.load_from_file(options.config_file)
            except Exception:
                logging.error("Could not read specified config file.")

        # Remember the rest of options
        for opt in ['nickname', 'server', 'port', 'channels']:
            val = getattr(options, opt)
            if val: setattr(self, opt, val)
        
        
    def load_from_file(self, file):
        '''
        Loads configuration from the specified YAML file.
        @param file: Name of the YAML file to load configuration from.
        '''
        try:
           
            # Read the file (or at least try to)
            import yaml
            file = open(file)
            cfg = yaml.load(file)
            
            # Parse the contents
            self.nickname = cfg.get("nickname", self.nickname)
            self.server = cfg.get("server", self.server)
            self.port = cfg.get("port", self.port)
            self.channels = cfg.get("channels", self.channels)
            self.cmd_prefix = cfg.get("command_prefix", self.cmd_prefix)
            self.commands = cfg.get("commands", self.commands)
            self.plugins = cfg.get("plugins", self.plugins)
            
        except Exception, e:
            
            logging.error("Could not load configuration from '%s':", file)
            try:    raise e
            except KeyError, e:     logging.error("Invalid file contents.")
            except IOError:         logging.error("File not found.")
            except ImportError:     logging.error("PyYAML library not found.")

        
###############################################################################
# Default configuration

# IRC options
NICKNAME = 'seejoo'
SERVER = 'irc.freenode.net'
PORT = 6667
CHANNELS = ['#cipra']

# Command options
PUBLIC_PREFIX = '.'
COMMANDS = ['seejoo.commands.standard', 'seejoo.commands.web']

# Plugin options
PLUGINS = ['seejoo.plugins.memo', 'seejoo.plugins.urlspy']


###############################################################################
# Config object

config = Config()
