from . import unittest, mock, CONFIG_EXAMPLE, builtins

from .. import util

sysinfo = {
    'meminfo': [
        'MemTotal:\t10000000 kB', # 10G, 10000M
        'MemFree:\t4000000 kB',
        'Buffers:\t1000000 kB',
        'Cached:\t4000000 kB'
    ],
    'cpuinfo': [
        'processor   : 0',
        'cpu MHz     : 1400.000',
        'cache size  : 2048 KB',
        'physical id : 0',
        'siblings    : 6',
        'core id     : 0',
        'cpu cores   : 3',
    ],
    'loadavg': ['0.01', '0.10', '1.00', '5/100', '1']
}

class TestParseMemInfo(unittest.TestCase):
    def setUp(self):
        self.meminfo = sysinfo['meminfo']
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
        self.assertEqual('4000000 kB', r['Cached'])

class TestGetCpuInfo(unittest.TestCase):
    def setUp(self):
        self.cpuinfo = sysinfo['cpuinfo']
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

class TestGetColonTab(unittest.TestCase):
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

class TestGetLoadavg(unittest.TestCase):
    def setUp(self):
        self.loadavg = sysinfo['loadavg']
        self.patch_open = mock.patch('redscheduler.util.open')
        self.mock_open = self.patch_open.start()
        self.addCleanup(self.patch_open.stop)

    def test_opens_proc_meminfo(self):
        util.get_loadavg()
        self.mock_open.assert_called_with('/proc/loadavg')

    def test_builds_dictionary_correctly(self):
        contents = '\t'.join(self.loadavg)
        self.mock_open.return_value.__enter__.return_value.read.return_value = contents
        r = util.get_loadavg()
        self.assertEqual(0.01, r['1min'])
        self.assertEqual(0.1, r['5min'])
        self.assertEqual(1.0, r['15min'])
        self.assertEqual('5/100', r['procs'])
        self.assertEqual('1', r['lastpid'])

class TestGetAvailmem(unittest.TestCase):
    def setUp(self):
        self.meminfo = util.parse_colon_tab('\n'.join(sysinfo['meminfo']))

    def test_returns_kilobytes(self):
        r = util.get_availmem(self.meminfo, 'K')
        self.assertEqual(9000000, r)

    def test_returns_megabytes(self):
        r = util.get_availmem(self.meminfo, 'M')
        self.assertEqual(9000, r)

    def test_returns_gigabytes(self):
        r = util.get_availmem(self.meminfo, 'G')
        self.assertEqual(9, r)

    def test_uneven_division(self):
        self.meminfo['MemFree'] = '3333333 kB'
        self.meminfo['Buffers'] = '1111111 kB'
        self.meminfo['Cached'] =  '1111111 kB'
        r = util.get_availmem(self.meminfo, 'M')
        self.assertEqual(5555, r)

    def test_invalid_unit_raises_exception(self):
        self.assertRaises(ValueError, util.get_availmem, self.meminfo, 'f')
