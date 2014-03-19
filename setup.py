#!/usr/bin/env python
"""
Setup script
"""
import os
import sys

from distutils.core import setup
from fedwatch import __version__

setup(
    name = 'fedwatch',
    description = 'Module for creating simple scripts reacting to fedmsg messages',
    version = __version__,
    license = 'LGPLv2+',
    py_modules = ['fedwatch'],
    scripts = ['bin/fedwatch'],
    url = 'https://github.com/sochotnicky/fedwatch',
    download_url = 'https://pypi.python.org/pypi/fedwatch',
    maintainer  = 'Stanislav Ochotnicky',
    maintainer_email = 'sochotnicky@redhat.com'
)
