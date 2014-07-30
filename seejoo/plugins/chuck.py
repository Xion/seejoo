'''
Created on Jan 7, 2012

@author: piotr
'''
import json
from urllib import urlencode

from seejoo.ext import plugin, Plugin
from seejoo.util.common import download


JOKES_URL = 'http://api.icndb.com/jokes/random'


@plugin
class Chuck(Plugin):
    commands = {
        'j': 'Says facts about Chuck Norris.'
    }

    def command(self, bot, channel, user, cmd, args):
        url = JOKES_URL
        if args:
            names = args.split(None, 1)
            url_params = {'firstName': names[0]}
            if len(names) > 1:
                url_params['lastName'] = names[1]
            url += '?' +  urlencode(url_params)

        jsonData = download(url)
        if not jsonData:
            return "Jokes not available at the moment."

        try:
            data = json.loads(jsonData)
        except ValueError:
            return "Jokes can not be parsed."

        joke = data.get("value", {}).get("joke")
        return joke or "Joke not found."
