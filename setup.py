#!/usr/bin/env python
try:
    import setuptools
    kw = dict(entry_points=dict(
        console_scripts=['2to3cache = lib2to3cache:main']))
except ImportError:
    kw = dict(scripts=["2to3cache"])

from distutils.core import setup

setup(name='lib2to3cache',
      version='0.1',
      py_modules=['lib2to3cache'],
      **kw)
