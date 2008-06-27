# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.


"""An example IRC log bot - logs a channel's events to a file.

If someone says the bot's name in the channel followed by a ':',
e.g.

  <foo> logbot: hello!

the bot will reply:

  <logbot> foo: I am a log bot

Run this script with two arguments, the channel name the bot should
connect to, and file to log to, e.g.:

  $ python ircLogBot.py test test.log

will log channel #test to the file 'test.log'.
"""


# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import urllib2
import sgmllib
import re
import time, sys

class BodyText(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        
        self.in_body = False
        
    def start_body(self, attrs):
        self.in_body = True

    def end_body(self):
        self.in_body = False

    def strip(self, some_html):
        self.theString = ""
        self.feed(some_html)
        self.close()
        return self.theString
		
    def handle_data(self, data):
        if self.in_body:
            self.theString += data


class CurryMenu:

    def __init__(self):
        self.menu = {}

        self.RE_ITEMS = re.compile(r'\(([0-9])\)(.*?)(\$\W*[0-9]\.[0-9][0-9])',
                                   re.S)

    def __getitem__(self, item):
        try:
            return self.menu[int(item)]
        except ValueError:
            raise KeyError()

    def load(self, url="http://mehfilindian.com/LunchMenuTakeOut.htm"):

        self._menu = urllib2.urlopen(url).read()
        self._menu_text = BodyText().strip(self._menu)
        
        for item in self.RE_ITEMS.findall(self._menu_text):
            self.menu[int(item[0])] = CurryMenuItem(item)

class CurryMenuItem:

    def __init__(self, item):
        items = (
                " ".join([n.strip() for n in item[1].strip().split('\n')]),
                item[2].strip())
        self.price = items[1]
        self.title, remainder = items[0].split('(')
        self.title = self.title.strip()
        self.summary, self.desc = remainder.split(')')
        self.desc = self.desc.strip()

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
    
    nickname = "currybot"
    
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
