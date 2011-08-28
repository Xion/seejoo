#!/usr/bin/env python
'''
Created on 2011-08-27

@author: xion

Setup script for the seejoo project.
'''
from setuptools import setup, find_packages
from seejoo.bot import Bot


setup(name = Bot.versionName,
      version = Bot.versionNum,
      description = 'IRC bot for geek-centered channels',
      author = 'Karol Kuczmarski',
      author_email = 'karol.kuczmarski@gmail.com',
      url = 'http://www.bitbucket.org/Xion/seejoo',
      license = 'Simplified BSD',
      classifiers = [
                     'Development Status :: 4 - Beta',
                     'Environment :: No Input/Output (Daemon)',
                     'Framework :: Twisted',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Information Technology',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2.6',
                     'Programming Language :: Python :: 2.7',
                     'Topic :: Communications :: Chat :: Internet Relay Chat',
                     'Topic :: Utilities',
                     ],
      
      requires = ['twisted'],
      extras_require = {
                        'config_file': ['yaml'],
                        },
      
      packages = find_packages('./src', exclude = ['test']),
      package_dir = { '': 'src' },
      scripts = ['src/seejoo/main.py'],
)
