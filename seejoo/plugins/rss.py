'''
Plugin for occasional polling of one or more RSS feeds.
@author Karol Kuczmarski
'''
from seejoo.ext import plugin, Plugin, get_storage_dir
from seejoo.util import irc
from datetime import datetime, timedelta
from lxml import etree
import urllib
import json
import os


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
          annouce_to: all # default
        - name: Other webpage feed
          url: http://otherwebpage.com/rss
          frequency: 30 seconds
          announce_to:
          - one_channel
          - other_channel
    '''
    DATA_FILE = 'feeds.json'

    def __init__(self):
        self.feeds = {}
        self.data_file = os.path.join(get_storage_dir(self), DATA_FILE)
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

    def tick(self, bot):
        ''' Called every second. Checks the feeds for new items. ''''
        now = datetime.now()
        if self.next_poll > now:
            return

        state = self._read_feeds_state(self)
        global_next_poll = None
        try:
            for st in state.iteritems():
                next_poll = self._poll_and_update_feed(*st)
                global_next_poll = (next_poll if not feeds_next_poll
                                    else min(next_poll, global_next_poll))
        finally:
            if global_next_poll:
                self.next_poll = global_next_poll
            self._save_feeds_state(state)


    def _poll_and_update_feed(self, name, state):
        ''' Polls the items from feed of given name and updates its state.
        @return: Time of the next scheduled poll for this feed
        '''
        feed = self.feeds[name]
        last_poll = datetime.fromtimestamp(st.get('last_poll_time', 0))
        frequency = feed['frequency']

        if last_poll + frequency <= datetime.now():
            items = poll_rss_feed(feed['url'], st.get('last_item'))
            self._announce_feed(name, items)
            st['last_poll_time'] = last_poll + frequency
            if items:
                st['last_item'] = items[0]['guid']

        return last_poll + frequency

    def _announce_feed(self, name, items):
        ''' Announces polled feed items to all target channels. '''
        feed = self.feeds[name]
        channels = feed['announce_to']
        if channels == 'all':
            channels = self.bot.channels

        for item in items:
            item_text = "@ %s -> % (by %s) <%s>" % (name, item['title'],
                                                    item.get('author', 'unknown'), item['link'])
            for channel in channels:
                irc.say(self.bot, channel, item_text)

    def _read_feeds_state(self):
        ''' Retrieves the state of feeds from data file. '''
        if not os.path.exists(self.data_file):
            return {}
        with open(self.data_file) as f:
            return json.load(f)

    def _save_feeds_state(self, state):
        ''' Saves the states of feeds to data file. '''
        with open(self.data_file, 'w') as f:
            json.dump(f)


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
    rss = etree.parse(urllib.urlopen(url))
    
    res = {}
    for channel in rss.iter('channel'):
        for item in channel.iter('item'):
            rss_item = dict((elem.tag, elem.text)
                            for elem in item.iter(tag=etree.Element)
                            if elem.tag != 'item')
            res.append(rss_item)

    return rss
