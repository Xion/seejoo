'''
Created on 2010-12-05

@author: xion

Configuration module. Contains code for reading the configuration
from command line and/or YAML file.
'''
from optparse import OptionGroup, OptionParser # Not argparse since we target Python 2.6 as well
import logging
import collections
import os


###############################################################################
# Config class

class Config(object):
    ''' Configuration class. Stores bot's settings, read from command line
    and/or YAML configuration file
    '''
    def __init__(self):
        self.set_defaults()
          
    def set_defaults(self):
        ''' Sets the default configuration settings. '''
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
        ''' Loads configuration settings from command line.
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
            except Exception, e:
                logging.error("Could not read specified config file '%s' (%s: %s)",
                              options.config_file, type(e).__name__, e)

        # Remember the rest of options
        for opt in ['nickname', 'server', 'port', 'channels']:
            val = getattr(options, opt, None)
            if val: setattr(self, opt, val)
        
        
    def load_from_file(self, filename):
        ''' Loads configuration from given file.
        @param filename: Config file. It must be in parseable format, e.g. JSON.
        '''
        if not os.path.isfile(filename):
            logging.error("Config file '%s' does not exist or is not a file")
            return

        parser = self.deduce_parser(filename)
        if not parser:
            logging.error("Unknown format of config file")
            return

        with open(filename) as cfg_file:
            cfg = parser.load(cfg_file)
            self.load(cfg)

    def deduce_parser(self, filename):
        ''' Infers the appropriate parser (object with load/loads/dump/dumps methods)
        that can be used to parse the file of given name.
        @return: Inferred parser object or None
        '''
        if not filename:
            logging.error("No filename provided to deduce parser")
            return

        _, extension = os.path.splitext(filename)
        if len(extension) <= 1:
            logging.error("Filename '%'s has no extension to deduce parser from", filename)
            return

        try:
            parser_name = extension[1:]
            parser = __import__(parser_name, globals(), locals())
        except ImportError:
            logging.error("Could not import parser module '%s'", parser_name)
            return

        return parser

    def load(self, cfg):
        ''' Loads configuration from specified dictionary.
        @param cfg: Dictionary which is a result of parsing a config file
        '''
        self.nickname = cfg.get("nickname", self.nickname)
        self.server = cfg.get("server", self.server)
        self.port = cfg.get("port", self.port)
        self.channels = cfg.get("channels", self.channels)
        self.cmd_prefix = cfg.get("command_prefix", self.cmd_prefix)
        self.commands = cfg.get("commands", self.commands)
        self.plugins = self.load_plugins(cfg)

    def load_plugins(self, cfg):
        ''' Processes the 'plugins' section of configuration file, if present.
        @return: Dictionary mapping names of plugin modules onto their configuration dicts
                 (or None, if no plugin-specific config has been supplied)
        '''
        plugins_section = cfg.get('plugins', self.plugins)
        if not plugins_section:
            return {}

        plugins = {}
        for plugin in plugins_section:
            if isinstance(plugin, collections.Mapping):
                plugin_module = plugin.get('module')
                if not plugin_module:
                    logging.warning("Invalid config entry in 'plugins' section: %s",
                                    plugin)
                    continue
                plugin_config = plugin.get('config')
            else:
                plugin_module = plugin
                plugin_config = None
            plugins[plugin_module] = plugin_config or None

        return plugins

        
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
PLUGINS = dict.fromkeys(['seejoo.plugins.memo', 'seejoo.plugins.urlspy'])


###############################################################################
# Config object

config = Config()
