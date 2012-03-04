For list of commands offered by the bot, see [help page](https://github.com/Xion/seejoo/wiki/Help).

seejoo
=
_seejoo_ is an IRC utility bot coded in Python and built upon the Twisted networking library.
Its main highlight is the extensible architecture: in most cases, new functionality can be added
by implementing custom **plugins**, rather than hacking the core code.
This approach also allows for customizing the specific bot instance to meet one'a particular needs.

The name _seejoo_ comes from the [lojban][jbo] word _sidju_ which roughly means 'to help'.


Installation
-
For updating convenience it's recommended to use <code>setup.py</code> with <code>develop</code> parameter:

    $ git clone git://github.com/Xion/seejoo.git
    $ cd seejoo
    $ sudo ./setup.py develop

This allows to simply <code>git pull</code> changes without having to run the <code>setup.py</code> script again.

_Note_: You will likely need to <code>sudo</code> the installation. If you are using a shell account and don't have
root access, you can use [virtualenv][venv] to create a personal copy of Python interpreter.


Running
-
Starting the bot as a simple as running:

    $ seejoo

However, you will likely want to customize the bot by providing a YAML configuration file:

    $ seejoo --config seejoo.yaml

See the attached *example_config.yaml* for supported config parameters.


Creating your own plugins
-
_Plugins_ are means for extending the bot's functionality. They are small programs which are driven
by the IRC-related events, such as someone joining a channel, saying something, changing channel's mode, and so on.
Plugins get notified about those events and can respond to them.

From the Python point of view, plugins are simple callables which get called when an event happens.
The simplest way to write a plugin is to subclass the <code>seejoo.ext.Plugin</code> class, which is shown
at the example below:

```python
from seejoo.ext import Plugin, plugin
from seejoo.util import irc
    
@plugin
class HelloResponder(Plugin):
    def message(self, bot, channel, user, message, msg_type):
        if not channel: return # Discarding non-channel messages
        
        # if user says something which resembles a greeting, respond to it
        msg = message.lower()
        if msg.startswith("hello") or msg.startswith("hi"):
            nick = irc.get_nick(user)
            response = "Hello %s!" % nick
            irc.say(bot, channel, response)
```            
Note that the class is decorated to with <code>@plugin</code> decorator. This is required as in principle,
plugins could also be normal functions.

For the list of interesting events you could handle in your plugin, see the definition of
<code>seejoo.ext.Plugin</code> class.

[jbo]: http://www.lojban.org
[venv]: http://pypi.python.org/pypi/virtualenv
