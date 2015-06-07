import json
import pickle
import os
import re
import codecs
from sys import maxint
import numpy as np
from sklearn.cluster import KMeans
from string import letters, digits, punctuation
from jellyfish import levenshtein_distance as levenshtein
from os.path import exists


class ReferenceStore():
    def __init__(self, filename, clusterfile):
        with open(filename, "rt") as file:
            self.data = json.load(file)
        self.samples = []
        if exists(clusterfile):
            with open(clusterfile, 'rb') as modelfile:
                self.cl = pickle.load(modelfile)
        else:
            self.cl = KMeans(n_clusters=2, n_jobs=-1)
            print 'Find clusters'
            i = 0
            traindata= []
            for id in self.data:
                i += 1
                samples = self.parse_one(self.data[id], train=True)
                if samples:
                    for ref in samples:
                        traindata.append([max(samples[ref])])
                        # traindata.extend([[item] for item in samples[ref]])
                print str(i) + '/' + str(len(self.data)), id
                if i == 2100:
                    break
            print traindata
            self.cl.fit(np.array(traindata))
            with open(clusterfile, 'wb') as modelfile:
                pickle.dump(self.cl, modelfile)

    def parse_one(self, item, train=False):
        if item["pdf"] == "No":
            return None
        filename = item["pdf"].split("/")[-1][:-3] + "txt"
        if filename not in os.listdir('../getpapers/data/convert'):
            res = os.spawnv(os.P_WAIT, 'convert.sh', ['', '../getpapers/data/convert/' + filename, '../getpapers/' + item["pdf"]])
            if res:
                print 'Something bad happened'
                return []
        try:
            refextr = ReferenceExtractor('../getpapers/data/convert/' + filename)
        except ValueError:
            print '\tCan\'t find References'
            return []
        refs = []
        table = {}
        # Begin finding references. Build table of assignings.
        for ref in item["refs"]:
            if ref not in self.data:
                table[ref] = []
                continue
            metadata = self.data[ref]["info"]
            if train:
                table[ref] = refextr.find_raw(metadata, table=True)
            else:
                refs.append({'name': refextr.find_raw(metadata, clusterizer=self.cl), 'attr': self.data[ref]['info']})
        # return refs
        if train:
            return table
        else:
            return table

    def parse(self):
        i = 0
        for id in self.data:
            i += 1
            samples = self.parse_one(self.data[id])
            if samples:
                self.samples.extend(samples)
            print str(i) + '/' + str(len(self.data)), id
            if i == 1:
            # if i == 2100:
                break

    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.samples, f)


class ReferenceExtractor():
    def __init__(self, filename):
        strings = []
        with codecs.open(filename, encoding="utf-8") as file:
            readed = file.readlines()
            while len(readed) > 0:
                strings.extend(readed)
                readed = file.readlines()
        strings = [filter(self.is_visible, str) for str in strings]
        strings = filter(lambda x: len(x) > 3, strings[len(strings) * 2 / 3:])
        min_dist = maxint
        ref_ind = 0
        for ind in xrange(len(strings)):
            dist = levenshtein(strings[ind].upper(), u'REFERENCES')
            if dist < min_dist:
                min_dist = dist
                ref_ind = ind
        if len(strings) <= ref_ind + 1 or u'REFERENCES' not in strings[ref_ind].upper().split(' '):
            raise ValueError('Can\'t find References')
        self.strings = [str.strip() for str in strings[ref_ind + 1:]]

    def get_table_row(self, metadata):
        row = []
        for ind in xrange(len(self.strings)):
            tokens = self.get_tokens(self.strings[ind])
            authors = []
            if "author" in metadata:
                authors = filter(lambda x: x != "AND", self.get_tokens(metadata["author"]))
            matches = self.num_of_matches(tokens, authors)
            row.append(matches * 1.0 / len(authors))
        return row

    def get_begin(self, row):
        return row.index(max(row))

    def find_raw(self, metadata, table=False, clusterizer=None):
        row = self.get_table_row(metadata)
        if not table:
            success_cluster = clusterizer.predict(1.0)[0]
            # filter bad assignings by clusterization
            for ind in xrange(len(row)):
                if clusterizer.predict(row[ind])[0] != success_cluster:
                    row[ind] = 0
            # normalize
            sum = reduce(lambda x,y: x + y, row)
            if not sum:
                sum = 1
            for ind in xrange(len(row)):
                row[ind] = row[ind] * 1.0 / sum
            # TODO Find best assignings
            # beginning of reference is found - it's 'beginning'
            beginning = self.get_begin(row)
            tokens = []
            index = beginning - 1
            reference_form_meta = filter(lambda x: x != "AND", self.get_tokens(metadata["author"]))
            reference_form_meta.extend(self.get_tokens(metadata['title']))
            if 'publisher' in metadata:
                reference_form_meta.extend(self.get_tokens(metadata['publisher']))
            if 'year' in metadata:
                reference_form_meta.extend(self.get_tokens(metadata['year']))
            if 'pages' in metadata:
                reference_form_meta.extend(self.get_tokens(metadata['pages']))
            prev_matches = -1
            matches = 0
            while matches > prev_matches:
                prev_matches = matches
                index += 1
                if len(self.strings) <= index:
                    break
                tokens.extend(self.get_tokens(self.strings[index]))
                matches = self.num_of_matches(tokens, reference_form_meta)

            # print 'Yay!'
            strings = self.strings[beginning:index]
            res = ' '.join(strings)

            return res
        else:
            return row
            # return max(row)

    def get_tokens(self, str):
        tmp = re.sub(" +", " ", str.strip())
        tokens = filter(lambda x: x not in punctuation or x is '-', tmp).upper().split(' ')
        return tokens

    def num_of_matches(self, where, matching):
        result = 0
        where.sort(key=len, reverse=True)
        flags = [True] * len(where)
        for token in matching:
            for ind in xrange(len(where)):
                if flags[ind] and token.startswith(where[ind]):
                    flags[ind] = False
                    result += 1
                    break
            # if token in where:
            #     result += 1
        return result

    def is_visible(self, symb):
        if symb in letters or symb in digits or symb in punctuation or symb == " ":
            return True
        else:
            return False


if __name__ == "__main__":
    # filename = "res.txt"
    # refextr = ReferenceExtractor(filename)
    # for str in refextr.strings:
    #     print str
    filename = "data/linked_papers.json"
    clusterfile = "data/threshold.model"
    refst = ReferenceStore(filename, clusterfile)

    # for key in refst.data.keys()[:2]:
    #     if refst.data[key]['refs']:
    #         print refst.data[key]['pdf']
    #         for ref in refst.data[key]['refs']:
    #             print '\t' + refst.data[ref]['info']['title']

    refst.parse()
    refst.save('data/samples.json')

