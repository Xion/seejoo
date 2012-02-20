'''
Plugin for occasional polling of one or more RSS feeds.
@author Karol Kuczmarski
'''
from seejoo.ext import plugin, Plugin, get_storage_dir
from datetime import datetime, timedelta
from lxml import etree
import urllib


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
    def __init__(self):
        self.feeds = {}
        self.dir = get_storage_dir(self)

    def init(self, bot, config):
        ''' Remembers the configuration of the plugin. '''
        feeds = config.get('feeds') if config else None
        if feeds:
            feeds = dict((f['name'], f) for f in feeds if 'name' in f)
        self.feeds = feeds or {}

    def tick(self, bot):
        ''' Called every second. Checks the feeds for new items. ''''
        pass


## Utility functions

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
