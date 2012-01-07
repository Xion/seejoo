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
            names = args.split(" ", 1)
            url_params = { 'firstName': names[0],
                           'lastName': names[1] if len(names) > 1 else '' }
            url += '?' +  urlencode(url_params)
            
        jsonData = download(url)
        if not jsonData:
            return "Jokes not available at the moment.";

        data = json.loads(jsonData)
        if not data:
            return "Jokes can not be parsed.";
        
        joke = data.get("value", {}).get("joke")
        return joke or "Joke not found."
