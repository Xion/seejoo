'''
Contains the URLSpy plugin, which provides functionality
related to URLs spoken by those present on IRC channel.
'''
import re

from seejoo.ext import plugin, Plugin
from seejoo.util.common import download
from seejoo.util.strings import normalize_whitespace


# Not entirely perfect regex but hey, it works :)
URL_RE = re.compile(r"((https?:\/\/)|(www\.))(\w+\.)*\w+(\/.*)*",
                    re.IGNORECASE)

TITLE_RE = re.compile(r'\<\s*title\s*\>(?P<title>.*?)\<\/\s*title\s*\>',
                      re.IGNORECASE | re.DOTALL)


@plugin
class URLSpy(Plugin):
    '''
    URLSpy plugin, providing various URL-related commands.
    '''
    commands = {
        't': 'Get a title of website with given or most recently said URL'
    }

    def __init__(self):
        ''' Initialization. '''
        self.urls = {}

    def message(self, bot, channel, user, message, type):
        '''
        Called when we hear a message being spoken.
        '''
        if not channel:
            return

        m = URL_RE.search(message)  # check if it there is an URL there
        if not m:
            return

        url = m.group(0)
        self.urls[channel] = url

    def command(self, bot, channel, user, cmd, args):
        '''
        Called when user issues a command.
        '''
        if not channel:
            return
        if cmd != 't':
            return

        url = args or self.urls.get(channel)
        if not url:
            return "I don't recall anything that looks like an URL."

        site = download(url)
        if not site:
            return "(Could not retrieve page)"

        m = TITLE_RE.search(site)
        if not m:
            return "(Untitled)"
        title = m.group('title')
        return normalize_whitespace(title)
