"""
Plugin for occasional polling of one or more RSS feeds.
@author Karol Kuczmarski
"""
import re
import logging
from datetime import datetime, timedelta
from itertools import takewhile

from lxml import etree
from dateutil.parser import parse as parse_date
import pytz

from seejoo.ext import plugin, Plugin
from seejoo.util import irc


@plugin
class Rss(Plugin):
    """ RSS polling plugin.

    Plugin should be configured with a list of RSS feeds that it should
    be polling. Here's an example of such configuration, which probably
    tells everything about how to do it::

        plugins:
        - module: seejoo.plugins.rss
          config:
            feeds:
            - name: Some webpage feed
              url: http://somewebpage.com/rss_feed
              frequency: 5 minutes
              filter:
              annouce: everywhere # default
            - name: Other webpage feed
              url: http://otherwebpage.com/rss
              frequency: 30 seconds
              announce:
              - one_channel
              - other_channel
    """
    def __init__(self):
        self.feeds = {}
        self.state = None
        self.next_poll = datetime.utcnow()  # will be in the past for the next tick()

    def init(self, bot, config):
        """ Remembers configuration of the plugin. """
        self.bot = bot

        feeds = config.get('feeds') if config else None
        if feeds:
            feeds = dict((f['name'], f) for f in feeds if 'name' in f)
            for f in feeds.itervalues():
                self._process_feed_config(f)

        self.feeds = feeds or {}
        self.state = dict((feed, {}) for feed in self.feeds.iterkeys())

    def _process_feed_config(self, f):
        """ Does a processing on feed configuration, preparing it
        to be used by the plugin.
        """
        freq = f.get('frequency', '5 minutes')
        f['frequency'] = parse_frequency(freq)

        filter_re = f.get('filter')
        if filter_re:
            f['filter'] = re.compile(filter_re)
        else:
            f.pop('filter', None)

        # fix the names of channels where feed updates shall be annouced
        announce = f.get('announce')
        if announce and not isinstance(announce, basestring):  # > 1 channel
            f['announce'] = [chan if chan.startswith('#') else '#' + chan
                             for chan in announce]

    def tick(self, bot):
        """ Called every second. Checks the feeds for new items. """
        if not self.state:
            return

        if self.next_poll > datetime.utcnow():
            return

        global_next_poll = None
        for st in self.state.iteritems():
            next_poll = self._poll_and_update_feed(*st)
            global_next_poll = (min(next_poll, global_next_poll)
                                if global_next_poll else next_poll)
        if global_next_poll:
            self.next_poll = global_next_poll

    def _poll_and_update_feed(self, name, state):
        """ Polls the items from feed of given name and updates its state.
        :return: Time of the next scheduled poll for this feed
        """
        feed = self.feeds[name]

        last_item = state.get('last_item')
        min_pub_date = state.get('last_poll_time') or datetime.utcnow()

        items = poll_rss_feed(feed['url'], until=lambda item: (
            item.get('guid') == last_item or
            item.get('pubDate', datetime.min) < min_pub_date)
        )
        if last_item:  # do not announce full feed
            self._announce_feed(name, items)

        state['last_poll_time'] = datetime.utcnow()
        if items:
            state['last_item'] = items[0]['guid']

        return datetime.utcnow() + feed['frequency']

    def _announce_feed(self, name, items):
        """ Announces polled feed items to all target channels. """
        feed = self.feeds[name]
        channels = feed.get('announce')
        if not channels or channels in ['everywhere', 'all']:
            channels = self.bot.channels

        for item in items:
            title = item['title']
            if 'filter' in feed and not feed['filter'].match(title):
                continue

            # don't display '(by X)' if there's no author
            author = item.get('authorName')
            by = " (by %s)" % author if author else ""

            item_text = "@ %s -> %s%s -- %s" % (name, title, by, item['link'])
            for channel in channels:
                irc.say(self.bot, channel, item_text)


# Utility functions

def parse_frequency(frequency):
    """ Parses the "frequency" configuration paramater, converting
    it to timedelta.
    :param frequency: Frequency string, e.g. "15 minutes", "4.5 hours"
    """
    if not frequency:
        return timedelta()

    try:
        count, unit = frequency.split()
        if not unit.endswith('s'):
            unit += 's'
        return timedelta(**{unit: float(count)})
    except (ValueError, TypeError):
        return timedelta()


def poll_rss_feed(feed_url, until=None):
    """ Polls an RSS feed, retrieving all new items
    up until a specific condition is met.

    :param until: Optional filter predicate for RSS items.
                  If specified, only items up to first one
                  that doesn't satisfy it will be returned.

    :return: List of RSS items, where each one is a dictionary
    """
    rss_items = get_rss_items(feed_url)
    if until is None:
        return rss_items

    return list(takewhile(lambda item: not until(item), rss_items))


def get_rss_items(url):
    """ Retrieves RSS items from given URL.

    .. note:: All <channel> elements are merged into flat list.

    :return: List of RSS items (dictionaries)
    """
    try:
        rss = etree.parse(url)
    except Exception:
        logging.exception("Error while downloading feed %s", url)
        return []

    # parse the RSS content
    res = []
    for channel in rss.getroot().iter('channel'):
        for item in channel.iter('item'):
            rss_item = dict((elem.tag, elem.text)
                            for elem in item.iter(tag=etree.Element)
                            if elem.tag != 'item')

            # conveniently convert pubDate to datetime objects,
            # in UTC but without timezone info (simplifies things later)
            try:
                pub_date = parse_date(rss_item['pubDate'])
                if pub_date.tzinfo is not None:
                    pub_date = pub_date.astimezone(pytz.utc)
                    pub_date = pub_date.replace(tzinfo=None)
                rss_item['pubDate'] = pub_date
            except (KeyError, ValueError):
                rss_item.pop('pubDate', None)  # remove if invalid

            res.append(rss_item)

    # sort it by date, descending
    return sorted(res,
                  key=lambda item: item.get('pubDate', datetime.min),
                  reverse=True)
