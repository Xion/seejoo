For list of commands offered by the bot, see [help page](https://github.com/Xion/seejoo/wiki/Help).

seejoo
=
_seejoo_ is an IRC utility bot coded in Python and built upon the Twisted networking library.
Its main highlight is the extensible architecture: in most cases, new functionality can be added
by implementing custom **commands** and **plugins**, rather than hacking the core code.
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
<code>seejoo.py</code> is the startup that can be invoked directly:

    $ ./seejoo.py

However, you will likely want to customize the bot by providing a YAML configuration file:

    $ ./seejoo.py --config seejoo.yaml

See the attached *example_config.yaml* for supported config parameters.


Extending
-
(Plugins & commands - to be expanded.)


[jbo]: http://www.lojban.org
[venv]: http://pypi.python.org/pypi/virtualenv
