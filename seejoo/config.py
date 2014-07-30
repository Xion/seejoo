'''
Created on 2010-12-05

@author: xion

Configuration module. Contains code for reading the configuration
from command line and/or a file.
'''
import collections
import logging
import os


# TODO: This is a singleton class so its members could be "flattened out"
# and put directly into root level of the module itself
class Config(object):
    ''' Configuration class. Stores bot's settings, read from command line
    and/or configuration file
    '''
    def __init__(self, cfg_file=None):
        self.set_defaults()
        if cfg_file:
            self.load_from_file(cfg_file)

    def set_defaults(self):
        ''' Sets the default configuration settings. '''
        self.server = 'irc.freenode.net'
        self.port = 6667
        self.ipv6 = False

        self.nickname = 'seejoo'
        self.nickserv_password = None
        self.nickserv_bot = 'NickServ'

        self.channels = ['#seejoo-test']

        self.cmd_prefix = '.'
        self.plugins = {}

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
            logging.error(
                "Filename '%'s has no extension to deduce parser from",
                filename)
            return

        try:
            parser_name = extension[1:]
            if parser_name == 'yml':
                parser_name = 'yaml'
            parser = __import__(parser_name, globals(), locals())
        except ImportError:
            logging.error("Could not import parser module '%s'", parser_name)
            return

        return parser

    def load(self, cfg):
        ''' Loads configuration from specified dictionary.
        @param cfg: Dictionary which is a result of parsing a config file
        '''
        self.server = cfg.get("server", self.server)
        self.port = cfg.get("port", self.port)
        self.ipv6 = cfg.get("ipv6", self.ipv6)

        self.nickname = cfg.get("nickname", self.nickname)
        self.nickserv_password = cfg.get("NickServ_password",
                                         self.nickserv_password)
        self.nickserv_bot = cfg.get("NickServ_bot_name", self.nickserv_bot)

        self.channels = cfg.get("channels", self.channels)

        self.cmd_prefix = cfg.get("command_prefix", self.cmd_prefix)
        self.plugins = self.load_plugins(cfg)

    def load_plugins(self, cfg):
        ''' Processes the 'plugins' section of configuration file, if present.

        :return: Dictionary mapping names of plugin modules
                 onto their configuration dicts
                 (or None, if no plugin-specific config has been supplied)
        '''
        plugins_section = cfg.get('plugins', self.plugins) or {}
        if isinstance(plugins_section, collections.Mapping):
            return plugins_section

        plugins = {}
        for plugin in plugins_section:
            if isinstance(plugin, collections.Mapping):
                plugin_module = plugin.get('module')
                if not plugin_module:
                    logging.warning(
                        "Invalid config entry in 'plugins' section: %s",
                        plugin)
                    continue
                plugin_config = plugin.get('config')
            else:
                plugin_module = plugin
                plugin_config = None
            plugins[plugin_module] = plugin_config or None

        return plugins


# Config object
config = Config()
