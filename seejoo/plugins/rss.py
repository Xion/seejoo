'''
Plugin for occasional polling of one or more RSS feeds.
@author Karol Kuczmarski
'''
from seejoo.ext import plugin, Plugin
from seejoo.util import irc
from datetime import datetime, timedelta
from lxml import etree
import time
import json
import logging


@plugin
class Rss(Plugin):
    ''' RSS polling plugin. 

    Plugin should be configured with a list of RSS feeds that it should
    be polling. Here's an example of such configuration, which probably
    tells everything about how to do it:

    plugins:
    - module: seejoo.plugins.rss
      config:
        feeds:
        - name: Some webpage feed
          url: http://somewebpage.com/rss_feed
          frequency: 5 minutes
          annouce: everywhere # default
        - name: Other webpage feed
          url: http://otherwebpage.com/rss
          frequency: 30 seconds
          announce:
          - one_channel
          - other_channel
    '''
    def __init__(self):
        self.feeds = {}
        self.state = None
        self.next_poll = datetime.now() # will be in the past for the next tick()

    def init(self, bot, config):
        ''' Remembers the configuration of the plugin. '''
        self.bot = bot

        feeds = config.get('feeds') if config else None
        if feeds:
            feeds = dict((f['name'], f) for f in feeds if 'name' in f)
            for f in feeds.itervalues():
                frequency = f.get('frequency', '5 minutes')
                f['frequency'] = parse_frequency(frequency)

        self.feeds = feeds or {}
        self.state = dict((feed, {}) for feed in self.feeds.keys())
        print self.feeds

    def tick(self, bot):
        ''' Called every second. Checks the feeds for new items. '''
        if not self.state: return

        now = datetime.now()
        if self.next_poll > now:
            return

        global_next_poll = None
        for st in self.state.iteritems():
            next_poll = self._poll_and_update_feed(*st)
            global_next_poll = (next_poll if not global_next_poll
                                else min(next_poll, global_next_poll))
        if global_next_poll:
            self.next_poll = global_next_poll


    def _poll_and_update_feed(self, name, state):
        ''' Polls the items from feed of given name and updates its state.
        @return: Time of the next scheduled poll for this feed
        '''
        feed = self.feeds[name]
        last_poll = state.get('last_poll_time', datetime.min)
        frequency = feed['frequency']

        if last_poll + frequency <= datetime.now():
            logging.debug("Polling RSS feed '%s'...", name)
            items = poll_rss_feed(feed['url'], state.get('last_item'))
            self._announce_feed(name, items)

            last_poll = datetime.now()
            state['last_poll_time'] = last_poll
            if items:
                logging.info("Found %s new items in '%s' feed", len(items), name)
                state['last_item'] = items[0]['guid']
            else:
                logging.debug("No new items found in '%s' feed", name)

        return last_poll + frequency

    def _announce_feed(self, name, items):
        ''' Announces polled feed items to all target channels. '''
        feed = self.feeds[name]
        channels = feed.get('announce')
        if not channels or channels in ['everywhere', 'all']:
            channels = self.bot.channels

        for item in items:
            item_text = "@ %s -> %s (by %s) <%s>" % (name, item['title'],
                                                     item.get('author', 'unknown'), item['link'])
            for channel in channels:
                irc.say(self.bot, channel, item_text)


## Utility functions

def parse_frequency(frequency):
    ''' Parses the "frequency" configuration paramater, converting
    it to timedelta.
    @param frequency: Frequency string, e.g. "15 minutes", "4.5 hours"
    '''
    if not frequency:
        return timedelta()

    try:
        count, unit = frequency.split()
        return timedelta(**{unit: float(count)})
    except (ValueError, TypeError), _:
        return timedelta()
    

def poll_rss_feed(feed_url, last_item=None):
    ''' Polls an RSS feed, retrieving all new items, up to but excluding
    the given last item.
    @param last_item: GUID of the last item we have polled from this feed
    @return: List of RSS items, where each one is a dictionary
    '''
    rss_items = get_rss_items(feed_url)

    if last_item:
        for item, i in enumerate(rss_items):
            guid = item.get('guid')
            if guid and guid == last_item:
                return rss_items[:i]

    return rss_items

def get_rss_items(url):
    ''' Retrieves RSS items from given URL.
    @note: All <channel> elements are merged into flat list.
    @return: List of RSS items (dictionaries)
    '''
    rss = etree.parse(url)
    
    res = []
    for channel in rss.getroot().iter('channel'):
        for item in channel.iter('item'):
            rss_item = dict((elem.tag, elem.text)
                            for elem in item.iter(tag=etree.Element)
                            if elem.tag != 'item')
            res.append(rss_item)

    return res
