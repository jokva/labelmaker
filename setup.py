#!/usr/bin/env python3

from setuptools import setup

setup(name='labelmaker',
    use_scm_version=True,
    description='Simple labeling tool for segyio files',
    long_description=open('README.md').read(),
    author='Statoil ASA',
    author_email='fg_gpl@statoil.com',
    entry_points = {
        'gui_scripts' : [ 'labelmaker = labelmaker:main' ]
    },
    packages=['labelmaker'],
    license='GPL-3.0',
    setup_requires=['pytest-runner', 'setuptools>=28', 'setuptools_scm'],
    tests_require=['pytest'],
    test_suite='pytest',
    install_requires=['matplotlib', 'segyio==1.4b1'],
    platforms='any',
)
