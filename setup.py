
from setuptools import setup, find_packages

setup(
    name = "currybot",
    version = "0.3",
    packages = find_packages('.'),

    # scripts and dependencies
    install_requires = ['setuptools',
                        'zope.interface',
                        'Twisted',
                        ],

    entry_points = { 'console_scripts':
                     [
                       'currybot = currybot:run',
                       'currybot-dev = currybot:run_dev',
                     ],
                   },

    # author metadata
    author = 'Creative Commons',
    author_email = 'software@creativecommons.org',
    description = 'IRC bot for the advancement of curry-related endeavours.',
    license = 'MIT',
    url = 'http://wiki.creativecommons.org/CurryBot',
    )
