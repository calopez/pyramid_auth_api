#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for tm.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 3.1.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import sys

from pkg_resources import require, VersionConflict
from setuptools import setup

try:
    require('setuptools>=38.3')
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)

# TODO: find out why we need to run pip-compile so: << echo "-e ." | pip-compile -o requirements.txt - >> instead of just pip-compile in order to pin the package versions
if __name__ == "__main__":
    setup(use_pyscaffold=True)
