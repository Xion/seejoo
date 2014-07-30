'''
Created on Jan 27, 2014

@author: MrPoxipol
'''
from __future__ import unicode_literals

import json
import urllib2

from seejoo.util.common import download
from seejoo.ext import plugin, Plugin


WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"


@plugin
class OpenWeather(Plugin):
    commands = {
        'f': ("Polls openweathermap.org for current weather "
              "information at specific place.")
    }

    def command(self, bot, channel, user, cmd, args):
        if not args:
            return

        url = WEATHER_URL + "?q=%s&lang=eng" % urllib2.quote(args)
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
        temperature = self._kelvins_to_celsius(data.get("main").get("temp"))

        wind_speed = self._mps_to_kmps(data.get("wind").get("speed"))
        wind_chill = self._calculate_wind_chill(temperature, wind_speed)

        msg = ("{city}, {country}: "
               "{temperature:.1f}^C -- {description}").format(**locals())
        if wind_chill is not None:
            msg = ("{city}, {country}: "
                   "{temperature:.1f}^C (felt as {wind_chill:.0f}^C) -- "
                   "{description}").format(**locals())
        return msg

    def _kelvins_to_celsius(self, temperature):
        return temperature - 273.15

    def _mps_to_kmps(self, velocity):
        return velocity * 3.6

    def _calculate_wind_chill(self, temperature, wind_speed):
        """Calculate wind chill. Can be None if temperature is high enough."""
        if temperature < 10 and (wind_speed / 3.6) >= 1.8:
            return (13.12 + 0.6215 * temperature
                    - 11.37 * pow(wind_speed, 0.16)
                    + 0.3965 * temperature * pow(wind_speed, 0.16))
