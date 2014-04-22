'''
Created on Jan 27, 2014

@author: MrPoxipol
'''
from seejoo.util.common import download
from seejoo.ext import plugin, Plugin
from unidecode import unidecode
import json
import urllib2

WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

@plugin
class OpenWeather(Plugin):
    commands = { 'weather': 'Fetches actual weather from openweathermap.org' }

    def command(self, bot, channel, user, cmd, args):
        if cmd != 'o':    return
        
        if args:
            url = WEATHER_URL
            url += "?q=" + urllib2.quote(args) + "&lang=eng"

            json_data = download(url)
            if not json_data:
                return "Weather not available at the moment."

            try:
                data = json.loads(json_data)
            except ValueError:
                self.error(bot, channel)
                return

            city = data.get("name")
            if not city:
                return "Could not find weather information."

            country = data.get("sys").get("country")
            description = data.get("weather")[0].get("description")
            temperature = data.get("main").get("temp")
            temperature -= 273.15 #From Kelvins to Celcious

            wind = data.get("wind").get("speed")
            wind *= 3.6 # m/s to km/h
            #Wind chill (only calculate if temperature is lower than 10^C and the wind speed is higher than 1.8 m/s)
            wchill = 0
            if temperature < 10 and (wind/3.6) >= 1.8:
                wchill = 13.12 + 0.6215*temperature - 11.37*pow(wind, 0.16) + 0.3965*temperature*pow(wind, 0.16)

            msg = u"***%s, %s: %d^C - %s" % (city, country, temperature, description)
            if wchill:
                msg = u"***%s, %s: %d^C (%d^C) - %s" % (city, country, temperature, wchill, description)

            msg = unidecode(msg)
            #msg = msg.encode("utf-8")
            return msg
