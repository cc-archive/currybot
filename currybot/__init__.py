# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import time, sys
import os
import cPickle as pickle

from currybot.currymenu import CurryMenu

class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""

    def __init__(self):
        self.nickname = "currybot"
        self.fn = "data.txt"
        if os.path.exists(self.fn):
            f = open(self.fn, 'rb')
            self.curryites = pickle.load(f)
            f.close()
        else:
            self.curryites = {}

    def _write_data(self):
        f = open(self.fn, 'wb')
        pickle.dump(self.curryites, f, 2)
        f.flush()
        f.close()
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" % 
                        time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        self.logger.close()

    @property
    def menu(self):

        try:
            return self._menu
        except AttributeError, e:
            self._menu = CurryMenu()
            self._menu.load()

        return self._menu

    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + " ") or \
                msg.startswith(self.nickname + ":") or \
                msg.startswith(self.nickname + ","):

            # get the "command" portion
            command = msg[len(self.nickname) + 1:].strip()

            if command == 'help':
                self.msg(channel, "No help here; guess you're SOL.")
                return

            if command == 'list':
                try:
                    for i in range(1,10):
                        item = self.menu[i]
                        self.msg(channel, '(%d) %s (%s)' %
                                  (i, item.title, item.summary))
                except KeyError:
                    return
                return

            if command == 'register':
                if self.curryites.has_key(user):
                    self.msg(channel, "%s is already a curryite!" % user)
                    return
                self.curryites[user] = None
                self.msg(channel, "%s has been registered as a curryite." %
                                                user)
                self._write_data()
                return

            if command == 'unregister':
                if self.curryites.has_key(user):
                    self.curryites.pop(user)
                    self.msg(channel, "%s is no longer a curryite." %
                                                user)
                else:
                    self.msg(channel, "%s wasn't a curryite to begin with!" % 
                                                user)
                self._write_data()
                return

            if command == 'curryites':
                # what a mess...
                if len(self.curryites) == 0:
                    self.msg(channel, "There is no curry cabal.")
                elif len(self.curryites) == 1:
                    self.msg(channel,
                        "%s is the only member of the curry cabal." %
                        self.curryites.keys()[0])
                elif len(self.curryites) == 2:
                    self.msg(channel,
                        "%s are members of the curry cabal." %
                        ' and '.join(self.curryites.keys()))
                else:
                    self.msg(channel,
                        "%s%s%s are members of the curry cabal." %
                       (', '.join(self.curryites.keys()[:-1]),
                        ', and ',
                        self.curryites.keys()[-1] ))
                return

            try:
                item = self.menu[command]
                self.msg(channel, "%s (%s) %s" %
                          (item.title, item.summary, item.desc))
                self.msg(channel, item.price)
                
            except KeyError, e:
                self.msg(channel, "%s: mmm... curry..." % user)

            # self.logger.log("<%s> %s" % (self.nickname, msg))

    #def action(self, user, channel, msg):
    #    """This will get called when the bot sees someone do an action."""
    #    user = user.split('!', 1)[0]
    #    self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = LogBot

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


def main(channel='cc', logfile='curry.log'):
    # initialize logging
    log.startLogging(sys.stdout)
    
    # create factory protocol and application
    f = LogBotFactory(channel, logfile)

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()

if __name__ == '__main__':
    main()
