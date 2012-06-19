'''
Created on Jan 7, 2012

@author: piotr
'''
from seejoo.util.common import download
from seejoo.ext import plugin, Plugin
from urllib import urlencode
import json


JOKES_URL = 'http://api.icndb.com/jokes/random'

@plugin
class Chuck(Plugin):
    commands = { 'j': 'Says facts about Chuck Norris.' }

    def command(self, bot, user, cmd, args):
        if cmd != 'j':    return
        
        url = JOKES_URL
        if args:
            names = args.split(None, 1)
            url_params = {'firstName': names[0]}
            if len(names) > 1:
                url_params['lastName'] = names[1]
            url += '?' +  urlencode(url_params)
            
        jsonData = download(url)
        if not jsonData:
            return "Jokes not available at the moment.";

        try:
            data = json.loads(jsonData)
        except ValueError:
            return "Jokes can not be parsed.";
        
        joke = data.get("value", {}).get("joke")
        return joke or "Joke not found."
