__author__ = 'dandelion'

import json
import re


class LogParser(object):
    def __init__(self, redirect_table):
        with open(redirect_table, 'r') as rtable:
            self.redirect_table = json.load(rtable)

    def parse(self, logfile):
        with open(logfile, 'r') as log:
            self.redirects = log.readlines()
        # finding all redirects
        self.redirects = filter(lambda x: re.findall('Redirecting', x), self.redirects)
        # from redirects extracting urls
        self.redirects = map(lambda x: re.findall('(?<=\<)[^\>]+(?=\>)', x), self.redirects)
        # from urls extracting cid & doi
        self.redirects = map(lambda x: map(lambda y: y.split('?')[-1], x), self.redirects)
        for redirect in self.redirects:
            # dict[cid] = doi
            self.redirect_table[redirect[1]] = redirect[0]
        print 'Yay!'

    def save(self, redirect_table):
        with open(redirect_table, 'w') as rtable:
            json.dump(self.redirect_table, rtable)


if __name__ == '__main__':
    datadir = 'data/'
    logparser = LogParser(datadir + 'rtable.json')
    logparser.parse(datadir + 'scrapy_log.txt')
    logparser.save(datadir + 'rtable.json')
