#!/usr/bin/env python
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def desc():
    info = read('README.rst')
    try:
        return info + '\n\n' + read('doc/changelog.rst')
    except IOError:
        return info

setup(
    name='sockjs-tornado',
    version='1.0.7',
    author='Serge S. Koval',
    author_email='serge.koval@gmail.com',
    packages=['sockjs', 'sockjs.tornado', 'sockjs.tornado.transports'],
    namespace_packages=['sockjs'],
    scripts=[],
    url='http://github.com/mrjoes/sockjs-tornado/',
    license='MIT License',
    description='SockJS python server implementation on top of Tornado framework',
    long_description=desc(),
    long_description_content_type='text/x-rst',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    requires=['tornado'],
    install_requires=[
        'tornado >= 4.0.0'
    ]
)
