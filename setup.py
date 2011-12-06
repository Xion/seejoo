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
      description = 'Extensible IRC bot for geek-centered channels',
      long_description = open("README.markdown").read(),
      author = 'Karol "Xion" Kuczmarski',
      author_email = 'karol.kuczmarski@gmail.com',
      url = 'http://github.com/Xion/seejoo',
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
      
      requires = ['twisted', 'pyyaml'],
      
      packages = find_packages(exclude = ['tests']),
      scripts = ['seejoo.py'],
)
