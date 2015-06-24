import unittest2 as unittest

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from os.path import join, dirname

import mock

# Example config
CONFIG_EXAMPLE = join(dirname(dirname(__file__)), 'redscheduler.config.example')

def json_response(json_):
    return mock.Mock(return_value=json_)
