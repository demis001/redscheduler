import os.path
import yaml

def load_config(configpath):
    '''
    Load yaml config from a path

    :param str configpath: Path to config
    :return: yaml dictionary
    '''
    return yaml.load(open(configpath))

def load_user_config():
    '''
    Loads config from user home directory
    
    :return: yaml dict
    '''
    p = os.path.join(os.path.expanduser('~/'), '.redscheduler.config')
    return load_config(p)
