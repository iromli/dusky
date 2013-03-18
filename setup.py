# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup  # NOQA


setup(
    name='dusky',
    description='Execute async MySQL queries within Tornado IOLoop',
    version='0.2.1',
    author='Isman Firmansyah',
    author_email='isman.firmansyah@gmail.com',
    url='https://github.com/iromli/dusky',
    py_modules=['dusky'],
    install_requires=['tornado', 'torndb'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
    ]
)
