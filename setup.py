# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='dusky',
    version='0.1.0',
    author='Isman Firmansyah',
    author_email='isman.firmansyah@gmail.com',
    url='https://github.com/iromli/dusky',
    py_modules=['dusky'],
    install_requires=['tornado', 'torndb']
)
