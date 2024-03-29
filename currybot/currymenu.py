
import urllib2
import sgmllib
import re

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

        # TODO: use regexes for scraping, or otherwise make this pretty
        count_parens = items[0].count('(')
        if count_parens == 0:
            self.price = items[1]
            self.desc = items[0]
            self.summary = 'NONE'
            self.title = "Couldn't parse"

        elif count_parens == 1:
            self.price = items[1]
            self.title, remainder = items[0].split('(')
            self.title = self.title.strip()
            self.summary, self.desc = remainder.split(')')
            self.desc = self.desc.strip()

        elif count_parens == 2:
            self.price = items[1]
            self.title, remainder = items[0].split('(', 1)
            self.title = self.title.strip()
            self.summary, self.desc = remainder.split(')', 1)
            self.desc = self.desc.strip()

        else:
            print "More than 2 parens, wtf?"

