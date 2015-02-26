from __future__ import print_function

from . import builtins
open = builtins.open

def parse_colon_tab(text):
    '''
    Parse text input that is in the form of (.*):(.*)
    and return a dictionary of all left side items as keys
    and right items as the value

    :param str text: text to parse
    ;return: dict
    '''
    _dict = {}
    for line in text.splitlines():
        l,r = line.split(':')
        _dict[l.strip()] = r.strip()
    return _dict

def get_mem_info():
    '''
    Read /proc/meminfo and return parsed results

    :return: dict of meminfo results
    '''
    with open('/proc/meminfo') as fh:
        contents = fh.read()
        mem_info = parse_colon_tab(contents)
    return mem_info

def get_cpu_info():
    '''
    Read /proc/cpuinfo and return parsed results
    :return: list of dict of cpuinfo results
    '''
    cpus = []
    with open('/proc/cpuinfo') as fh:
        contents = fh.read()
        for cpu in contents.split('\n\n'):
            cpus.append(parse_colon_tab(cpu))
    return cpus

def get_loadavg():
    '''
    Read /proc/loadavg and return as a dict of
    {'1min', '5min', '15min', 'procs', 'lastpid'} 

    :return: dict of meminfo results
    '''
    loadavg = {}
    with open('/proc/loadavg') as fh:
        parts = fh.read().strip().split()
        loadavg['1min'] = float(parts[0])
        loadavg['5min'] = float(parts[1])
        loadavg['15min'] = float(parts[2])
        loadavg['procs'] = parts[3]
        loadavg['lastpid'] = parts[4]
    return loadavg

def get_availmem(meminfo, unit='K'):
    '''
    Return the ammount of memory that is really free
    MemFree + Buffers + Cached

    :param dict meminfo: get_mem_info dictionary
    :param str unit: Unit to return free memory in valid values ('K','M',G)
    :return: int of how much free memory(in units)
    '''
    unit_map = {
        'K': 1,
        'M': 1000,
        'G': 1000000
    }
    if unit not in unit_map:
        raise ValueError('{0} is not a valid unit identifier'.format(unit))
    avail = [meminfo['MemFree'], meminfo['Buffers'], meminfo['Cached']]
    avail = sum(map(lambda x: int(x.split()[0]), avail))
    return int(avail / unit_map[unit])
