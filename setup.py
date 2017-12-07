#!/usr/bin/env python3

from setuptools import setup

setup(name='labelmaker',
      description='Simple labeling tool for segyio files',
      long_description=open('README.md').read(),
      author='Statoil ASA',
      author_email='fg_gpl@statoil.com',
      #url='https://github.com/Statoil/segyviewer',
      scripts=['main.py'],
      license='LGPL-3.0',
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      platforms='any',
      )
