'''
Created on 2014-05-22

@author: MrPoxipol

IMDB/Open Movie DB plugin
'''

from __future__ import unicode_literals

import json
import urllib2
import re

from seejoo.util.common import download
from seejoo.ext import plugin, Plugin


API_URL = "http://www.omdbapi.com/"


@plugin
class Imdb(Plugin):
    commands = {
        'im': ("Polls Open Movie Database for "
               "informations about specified movie.")
    }

    def command(self, bot, channel, user, cmd, args):
        if cmd != 'im':
            return
        if not args:
            return

        title = ''
        year = ''
        try:
            m = re.search(r"\s+\((\d+)\)", args)
            year = m.group(1) # '2005'

            # Remove year from args
            title = args[:m.start()] + args[m.end():]
        except Exception:
            title = args
            year = ''

        url = API_URL + "?t=%s&y=%s" % (urllib2.quote(title), year)
        json_data = download(url)
        if not json_data:
            return "IMDB not available at the moment."

        try:
            data = json.loads(json_data)
        except ValueError:
            self.error(bot, channel)
            return

        title = data.get("Title")
        if not title:
            return "Could not find movie."

        year = data.get("Year")
        genre = data.get("Genre")
        actors = data.get("Actors")
        plot = data.get("Plot")
        country = data.get("Country")
        rating = data.get("imdbRating")
        type = data.get("Type")

        message = "[{title} ({year}, {country}) {genre}/{type}] {rating}/10 - Starring: {actors}: {plot}".format(**locals())
        return message
