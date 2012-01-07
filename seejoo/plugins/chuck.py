'''
Created on Jan 7, 2012

@author: piotr
'''
from seejoo.util.common import download
import json
from seejoo.ext import plugin, Plugin

@plugin
class Chuck(Plugin):
    
    commands = { 'j': 'Says facts about Chuck Norris.' }

    def __init__(self):
        '''
        Constructor
        '''
    def command(self, bot, user, cmd, args):
        if cmd != 'j':    return
        
        if args:
            names = args.split(" ", 2)
            if(len(names) == 1):
                jsonData = download("http://api.icndb.com/jokes/random?firstName=" + names[0] + "&lastName=")
            else:
                jsonData = download("http://api.icndb.com/jokes/random?firstName=" + names[0] + "&lastName=" + names[1])
        else:
            jsonData = download("http://api.icndb.com/jokes/random")
        if not jsonData:
            return "Jokes not available at the moment.";
        data = json.loads(jsonData)
        if not data:
            return "Jokes can not be parsed.";
        
        joke = data["value"]["joke"]
        if not joke:
            return "Joke not found"
        return joke