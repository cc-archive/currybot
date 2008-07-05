
from twisted.internet import reactor
from twisted.python import log

import sys

from currybot.irc import BotFactory


def start_bot(channel, logfile='curry.log'):
    # initialize logging
    log.startLogging(sys.stdout)
    
    # create factory protocol and application
    f = BotFactory(channel, logfile)

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()

def run():
    start_bot(channel='cc')

def run_dev():
    start_bot(channel='cc-currybot', logfile='currydev.log')
