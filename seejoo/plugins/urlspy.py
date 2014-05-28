"""
Contains the URLSpy plugin, which provides functionality
related to URLs spoken by those present on IRC channel.
"""
import logging
import re

from bs4 import BeautifulSoup

from seejoo.ext import plugin, Plugin
from seejoo.util import irc
from seejoo.util.common import download
from seejoo.util.strings import normalize_whitespace


TITLE_MAX_LEN = 250

URL_RE = re.compile(r"""
    ((https?\:\/\/)|(www\.))    # URLs start with http://, https:// or www.
    (\w+\.)*\w+                 # followed by domain/host part
    (\/[^\s\/]+)*\/?            # and an optional path part
    """, re.IGNORECASE | re.VERBOSE)

YOUTUBE_URL_RE = re.compile(
    r'(https?://)?(www\.)?youtube\.(\w+)/watch\?v=([-\w]+)', re.IGNORECASE)


@plugin
class URLSpy(Plugin):
    """Plugin for listening on users pasting URLs and automatically resolving
    where they point to.
    """
    def message(self, bot, channel, user, message, type):
        """Called when we hear a message being spoken."""
        if not channel or channel == '*':
            return
        # if message comes from server
        if '!' not in user:
            return

        if irc.get_nick(user) == bot.nickname:
            return

        url_match = URL_RE.search(message)
        if url_match:
            result = self._resolve_url(url_match.group(0))
            if result:
                type_, title = result
                irc.say(bot, channel, u"[%s] %s" % (type_, title))

    def _resolve_url(self, url):
        """Handle URL being spoken on a channel where the bot is."""
        page_content = download(url)
        if not page_content:
            logging.debug("Could not download URL %s" % url)
            return

        html = BeautifulSoup(page_content)
        if YOUTUBE_URL_RE.match(url):
            return self._handle_youtube_video(html)
        else:
            return self._handle_regular_page(html)

    def _handle_youtube_video(self, html):
        """Special handling of Youtube URLs: shows video title
        and watch counter value.
        """
        try:
            title = sanitize(html.find('span', id='eow-title').text)
            watch_tag = sanitize(html.find('span', class_='watch-view-count').text)
            watch_count = ' '.join(re.findall(r'(?=\d)[\d\s]+(?<=\d)', watch_tag))
        except AttributeError:
            return "YouTube", "(Unknown video)"
        else:
            return "YouTube", "%s (watched %s times)" % (title, watch_count)

    def _handle_regular_page(self, html):
        """Handle regular page by displaying its <title>."""
        try:
            title = sanitize(html.find('title').text)
            # Title length limit
            title = shorten(title)
            return "", title
        except AttributeError:
            pass


def shorten(text):
    if len(text) < TITLE_MAX_LEN:
        return text

    word_wrap = text[:TITLE_MAX_LEN].rfind(' ')
    word_wrap = 250 if word_wrap == -1 else word_wrap

    text = text[:word_wrap] + '..'
    return text


def sanitize(text):
    """Sanitize text extracted from HTML"""
    return normalize_whitespace(text).strip()
