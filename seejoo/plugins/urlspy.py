'''
Contains the URLSpy plugin, which provides functionality
related to URLs spoken by those present on IRC channel.
'''
from seejoo.ext import plugin, Plugin
from seejoo.util.common import download
import re
from seejoo.util.strings import normalize_whitespace


# Not entirely perfect regex but hey, it works :)
URL_RE = re.compile(r"((https?:\/\/)|(www\.))(\w+\.)*\w+(\/.*)*", re.IGNORECASE)

TITLE_RE = re.compile(r'\<\s*title\s*\>(?P<title>.*?)\<\/\s*title\s*\>', re.IGNORECASE | re.DOTALL)


@plugin
class URLSpy(Plugin):
    '''
    URLSpy plugin, providing various URL-related commands.
    '''
    commands = { 't': 'Get a title of website with given or most recently said URL' }
    
    def __init__(self):
        ''' Initialization. '''
        self.last_url = None
    
    def message(self, bot, channel, user, message, type):
        '''
        Called when we hear a message being spoken.
        '''
        if not channel: return
        
        m = URL_RE.search(message) # Check if it there is an URL there
        if not m:   return

        url = m.group(0)
        self.last_url = url

    def command(self, bot, user, cmd, args):
        '''
        Called when user issues a command.
        '''
        if cmd == 't':
            
            url = args or self.last_url
            if not url: return "I don't recall anything that looks like an URL."

            # Download the page
            site = download(url)     
            if not site:    return "(Could not retrieve page)"
            
            # Find the title and return it
            m = TITLE_RE.search(site)
            if not m:   return "(Untitled)"
            title = m.group('title')
            return normalize_whitespace(title)
