from setuptools import setup, find_packages

from redscheduler import __version__, __projectname__

setup(
    name = __projectname__,
    version = __version__,
    packages = find_packages(),
    install_requires = [],
    author = 'Tyghe Vallard',
    author_email = 'vallardt@gmail.com',
    description = 'Use redmine to manage sample data',
    license = 'GPL v2',
    keywords = 'inventory, sample, management, redmine',
    url = 'https://github.com/VDBWRAIR/redscheduler',
    entry_points = {
        'console_scripts': [
            'runissue = redscheduler.runissue:main',
        ]
    }
)
