from . import unittest, mock, json_response, CONFIG_EXAMPLE, builtins

from os.path import *
import tempfile

from .. import config

class TestGetConfig(unittest.TestCase):
    def test_loads_config(self):
        r = config.load_config(CONFIG_EXAMPLE)
        keys = (
            'siteurl', 'apikey', 'jobscheduleproject'
        )
        for key in keys:
            self.assertIn(key, r)

class TestLoadUserConfig(unittest.TestCase):
    def test_loads_from_homedir_path(self):
        with mock.patch.object(config, 'yaml') as mock_yaml:
            with mock.patch.object(builtins, 'open') as mock_open:
                c = config.load_user_config()
                homeconf = expanduser('~/.redscheduler.config')
                self.assertEqual(
                    homeconf,
                    mock_open.call_args_list[0][0][0]
                )
