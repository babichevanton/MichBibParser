import json
from string import punctuation
from sys import maxint
from nltk.metrics.distance import edit_distance


class DataStore():
    def __init__(self):
        self.baseitems = []

    def init_base(self, filename, numofitems):
        with open(filename, "rt") as datafile:
            data = json.load(datafile)
        if numofitems < len(data):
            itemcount = numofitems
        else:
            itemcount = len(data)
        for i in xrange(itemcount):
            name = data[i]["name"].strip().upper()
            attributes = data[i]["attr"]
            attrs = {}
            if 'author' in attributes:
                attrs['author'] = attributes['author'].upper()
            else:
                attrs['author'] = ''
            if 'title' in attributes:
                attrs['title'] = attributes['title'].upper()
            else:
                attrs['title'] = ''
            if 'publisher' in attributes:
                attrs['publisher'] = attributes['publisher'].upper()
            else:
                attrs['publisher'] = ''
            if 'year' in attributes:
                attrs['year'] = attributes['year'].upper()
            else:
                attrs['year'] = ''
            if 'pages' in attributes:
                attrs['pages'] = attributes['pages'].upper()
            else:
                attrs['pages'] = ''
            self.baseitems.append((name, attrs))
        return self

    def get_base(self):
        return [item[1] for item in self.baseitems]

    def get_names(self):
        return [item[0] for item in self.baseitems]

    def print_base(self):
        for item in self.baseitems:
            print item[0]
            for key, value in item[1].iteritems():
                print "    ", key, ":", value
        return self


class Post():
    def __init__(self, string):
        self.content = string.strip().upper()

    def find_attr(self, attr):
        result = "BUG"
        mindist = maxint
        window_size = len(attr.split(" "))
        tokens = filter(lambda x: x not in punctuation or x is '-', self.content).upper().split(" ")
        attr_toks = filter(lambda x: x not in punctuation or x is '-', attr).upper()
        for i in xrange(len(tokens) - window_size):
            for j in range(window_size + 1)[-1::-1]:
                cand = ""
                for k in xrange(window_size + 1):
                    if k != j:
                        cand += tokens[i + k] + " "
                cand = cand.strip()
                dist = edit_distance(cand, attr_toks)
                if dist < mindist:
                    mindist = dist
                    result = cand
        return result

    def print_cont(self):
        print self.content
        return self
