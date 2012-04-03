#!/usr/bin/env python
import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

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

setup(
    name='sockjs-tornado',
    version='0.0.3',
    author='Serge S. Koval',
    author_email='serge.koval@gmail.com',
    packages=['sockjs', 'sockjs.tornado', 'sockjs.tornado.transports'],
    namespace_packages=['sockjs'],
    scripts=[],
    url='http://github.com/MrJoes/sockjs-tornado/',
    license=license,
    description='SockJS python server implementation on top of Tornado framework',
    long_description=desc(),
    requires=['tornado'],
    install_requires=[
        'tornado >= 2.1.1'
    ]
)
