#!/usr/bin/env python
'''
Created on 2011-08-27

@author: xion

Setup script for the seejoo project.
'''
import ast
import os
from setuptools import setup, find_packages


def read_tags(filename):
    """Reads values of "magic tags" defined in the given Python file.

    :param filename: Python filename to read the tags from
    :return: Dictionary of tags
    """
    with open(filename) as f:
        ast_tree = ast.parse(f.read(), filename)

    res = {}
    for node in ast.walk(ast_tree):
        if type(node) is not ast.Assign:
            continue

        target = node.targets[0]
        if type(target) is not ast.Name:
            continue

        if not (target.id.startswith('__') and target.id.endswith('__')):
            continue

        name = target.id[2:-2]
        res[name] = ast.literal_eval(node.value)

    return res


tags = read_tags(os.path.join('seejoo', '__init__.py'))


setup(
    name="seejoo",
    version=tags['version'],
    description='Extensible IRC bot for geek-centered channels',
    long_description=open("README.markdown").read(),
    author=tags['author'],
    url='http://github.com/Xion/seejoo',
    license=tags['license'],

    classifiers=[
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

    install_requires=open('requirements.txt').readlines(),

    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': ['seejoo=seejoo.main:main']
    },
)
