#!/usr/bin/env python
import setuptools
from distutils.core import setup

setup(name='lib2to3cache',
      version='0.1',
      py_modules=['lib2to3cache'],
      entry_points = dict(console_scripts=['2to3cache = lib2to3cache:main']),
      )
