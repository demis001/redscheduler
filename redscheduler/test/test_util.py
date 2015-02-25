from . import unittest, mock, CONFIG_EXAMPLE, builtins

from .. import util

class TestParseMemInfo(unittest.TestCase):
    def setUp(self):
        self.meminfo = [
            'MemTotal:\t10000000 kB',
            'MemFree:\t4000000 kB',
            'Buffers:\t1000000 kB',
            'Cached:\t5000000 kB'
        ]
        self.patch_open = mock.patch('redscheduler.util.open')
        self.mock_open = self.patch_open.start()
        self.addCleanup(self.patch_open.stop)

    def test_opens_proc_meminfo(self):
        util.get_mem_info()
        self.mock_open.assert_called_with('/proc/meminfo')

    def test_parses_meminfo(self):
        self.mock_open.return_value.__enter__.return_value.read.return_value = \
            '\n'.join(self.meminfo)
        r = util.get_mem_info()
        self.assertEqual('10000000 kB', r['MemTotal'])
        self.assertEqual('4000000 kB', r['MemFree'])
        self.assertEqual('1000000 kB', r['Buffers'])
        self.assertEqual('5000000 kB', r['Cached'])

class TestParseCpuInfo(unittest.TestCase):
    def setUp(self):
        self.cpuinfo = [
            'processor   : 0',
            'cpu MHz     : 1400.000',
            'cache size  : 2048 KB',
            'physical id : 0',
            'siblings    : 6',
            'core id     : 0',
            'cpu cores   : 3',
        ]
        self.patch_open = mock.patch('redscheduler.util.open')
        self.mock_open = self.patch_open.start()
        self.addCleanup(self.patch_open.stop)

    def test_opens_proc_meminfo(self):
        util.get_cpu_info()
        self.mock_open.assert_called_with('/proc/cpuinfo')

    def test_parses_meminfo(self):
        contents = '\n'.join(self.cpuinfo) + '\n\n' + '\n'.join(self.cpuinfo)
        self.mock_open.return_value.__enter__.return_value.read.return_value = contents
        r = util.get_cpu_info()
        self.assertEqual(2, len(r))
        self.assertIn('processor', r[0])
        self.assertIn('processor', r[1])

class TestParseColonTab(unittest.TestCase):
    def test_parses_returns_dictionary(self):
        colontab = [
            'foo1:bar',
            'foo2: bar',
            'foo3:\tbar',
            'foo4 :\t bar baz\t '
        ]
        r = util.parse_colon_tab('\n'.join(colontab))
        self.assertEqual('bar', r['foo1'])
        self.assertEqual('bar', r['foo2'])
        self.assertEqual('bar', r['foo3'])
        self.assertEqual('bar baz', r['foo4'])
