#!/usr/bin/env python
import os

import distutils.core
import sys

try:
    import setuptools
except ImportError:
    pass

try:
    license = open('LICENSE').read()
except:
    license = None


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def desc():
    info = read('README.rst')
    try:
        return info + '\n\n' + read('doc/changelog.rst')
    except IOError:
        return info

distutils.core.setup(
    name='sockjs-tornado',
    version='1.0.0',
    author='Serge S. Koval',
    author_email='serge.koval@gmail.com',
    packages=['sockjs', 'sockjs.tornado', 'sockjs.tornado.transports'],
    namespace_packages=['sockjs'],
    scripts=[],
    url='http://github.com/mrjoes/sockjs-tornado/',
    license=license,
    description='SockJS python server implementation on top of Tornado framework',
    long_description=desc(),
    requires=['tornado'],
    install_requires=[
        'tornado >= 2.1.1'
    ]
)
