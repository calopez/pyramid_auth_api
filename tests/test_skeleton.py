#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from tm.skeleton import fib

__author__ = "Carlos Andres Lopez"
__copyright__ = "Carlos Andres Lopez"
__license__ = "mit"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
