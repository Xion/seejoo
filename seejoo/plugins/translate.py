"""
Plugin for translation of phrases using Google Translate.

.. warning:: This is highly experimental and hackish,
             and fragile, and might break horribly,
             and come back to haunt you at night.
"""
from __future__ import unicode_literals

from collections import namedtuple
from itertools import dropwhile, takewhile
import json
from urllib import urlencode

from taipan.collections import dicts

from seejoo.ext import plugin, Plugin
from seejoo.util.common import download


DEFAULT_TARGET_LANGUAGE = 'en-US'
MAX_LANGUAGE_CODE_LEN = 7


@plugin
class Translate(Plugin):
    """Translation plugin."""
    commands = {
        'tr': "Translate given phrase using Google Translate API."
    }

    def __init__(self):
        self._default_source_lang = None  # autodetection
        self._default_target_lang = DEFAULT_TARGET_LANGUAGE
        self._lang_prefix = None  # command prefix by default

    def init(self, bot, config):
        """Remembers configuration for the plugin."""
        self._default_source_lang = dicts.get(
            config,
            ('default_source', 'default_source_lang', 'default_source_language'),
            self._default_source_lang)
        self._default_target_lang = dicts.get(
            config,
            ('default_target', 'default_target_lang', 'default_target_language'),
            self._default_target_lang)
        self._lang_prefix = dicts.get(
            config,
            ('lang_prefix', 'language_prefix'),
            self._lang_prefix or bot.config.cmd_prefix)

    def command(self, bot, channel, user, cmd, args):
        """Reacts to translation command."""
        args = args.strip()
        if not args:
            return "No text specified"

        arg_parts = args.split()

        # determine source and target languages from command argument parts
        source_lang = self._default_source_lang
        target_lang = self._default_target_lang
        langs = list(takewhile(self._is_lang_flag, arg_parts))
        if langs:
            if len(langs) == 1:
                target_lang = langs[0].lstrip(self._lang_prefix)
            elif len(langs) == 2:
                source_lang = langs[0].lstrip(self._lang_prefix)
                target_lang = langs[1].lstrip(self._lang_prefix)
            else:
                return "Invalid language arguments"

        text = " ".join(dropwhile(self._is_lang_flag, arg_parts))
        translation = fetch_translation(text, target_lang, source_lang)
        return "{translated_text} ({source_lang} -> {target_lang})".format(
            **translation.__dict__)

    def _is_lang_flag(self, s):
        """Whether given string specifies an input or output language."""
        return isinstance(s, basestring) and \
            s.startswith(self._lang_prefix) and \
            1 < len(s.lstrip(self._lang_prefix)) < MAX_LANGUAGE_CODE_LEN


#: Represents a translation of a phrase.
Translation = namedtuple('Translation', ['source_lang', 'original_text',
                                         'target_lang', 'translated_text'])


# Google Translate API calls

API_ENDPOINT_URL = 'http://translate.google.com/translate_a/t'
FIXED_API_PARAMS = {
    'client': 't',
    'multires': 1,
    'otf': 1,
    'ssel': 0,
    'tsel': 0,
    'uptl': 'en',
    'sc': 1,
}
USER_AGENT = "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"


def get_translate_url(text, target_lang, source_lang=None):
    """Format URL for translating given test from source to target language."""
    query_args = dicts.merge(FIXED_API_PARAMS, {
        'sl': source_lang or 'auto',
        'tl': target_lang,
        'text': text,
    })
    return API_ENDPOINT_URL + '?' + urlencode(query_args)


def fetch_translation(text, target_lang, source_lang=None):
    """Get the translation of given text and return as Translation tuple."""
    url = get_translate_url(text, target_lang, source_lang)
    response = download(url, user_agent=USER_AGENT)

    # convert the protobuf wire format to something json module can swallow
    while ',,' in response:
        response = response.replace(',,', ',null,')
    data = json.loads(response)[0]

    # read the actual source language, which may have been autodetected
    try:
        source_lang = data[2]
    except IndexError:
        source_lang = source_lang or "?"

    return Translation(
        source_lang=source_lang,
        original_text=data[0][1],
        target_lang=str(target_lang).lower(),
        translated_text=data[0][0],
    )
