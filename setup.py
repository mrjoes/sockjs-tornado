#!/usr/bin/env python

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

try:
    readme = open('README.rst').read()
except:
    readme = None

setup(
    name='sockjs-tornado',
    version='0.0.1',
    author='Serge S. Koval',
    author_email='serge.koval@gmail.com',
    packages=['sockjs', 'sockjs.tornado', 'sockjs.tornado.transports'],
    namespace_packages=['sockjs'],
    scripts=[],
    url='http://github.com/MrJoes/sockjs-tornado/',
    license=license,
    description='SockJS pyton server implementation on top of Tornado framework',
    long_description=readme,
    requires=['tornado'],
    install_requires=[
        'tornado >= 2.1.1'
    ]
)
