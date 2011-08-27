#!/usr/bin/env python

'''
Created on 2011-08-27

@author: xion

Setup script for the seejoo project.
'''
from setuptools import setup, find_packages


setup(name = 'seejoo',
      version = '1.0',
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
      
      install_requires = ['twisted'],
      packages = find_packages('./src', exclude = ('test',)),
      package_dir = { 'seejoo': 'src/seejoo' },
      scripts = ['src/seejoo/main.py'],
)
