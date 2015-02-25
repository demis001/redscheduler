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
    :return: dict of cpuinfo results
    '''
    cpus = []
    with open('/proc/cpuinfo') as fh:
        contents = fh.read()
        for cpu in contents.split('\n\n'):
            cpus.append(parse_colon_tab(cpu))
    return cpus
