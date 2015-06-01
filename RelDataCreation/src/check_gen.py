from copy import copy
import json
from string import punctuation
from string import find as substr
from sys import maxint
from jellyfish import levenshtein_distance as levenshtein
import re


def find_attr(post, attr):
    if attr == '':
        return []

    result = []
    res_cand = 'BUG'
    mindist = maxint
    window_size = len(attr.split(' '))
    punct = punctuation
    punct.replace('-', '')
    for char in filter(post.__contains__, punct):
        post.replace(char, u' ')
    tokens = filter(lambda x: x not in punctuation or x is '-', post).upper().split(" ")
    tokens = zip(tokens, range(len(tokens)))

    for i in xrange(len(tokens) - window_size):
        for j in range(window_size + 1)[-1::-1]:
            cand = ''
            cand_ind = []
            for k in xrange(window_size + 1):
                if k != j:
                    cand += tokens[i + k][0] + ' '
                    cand_ind.append(tokens[i + k][1])
            cand = cand.strip()
            dist = levenshtein(unicode(cand), unicode(attr.upper()))
            if dist < mindist:
                mindist = dist
                result = cand_ind
                res_cand = cand
    res = zip(res_cand.split(), result)
    temp = copy(res)
    for tok in temp:
        if substr(attr.upper(), tok[0]) < 0:
            res.remove(tok)
    return map(lambda x: x[1], res)


if __name__ == '__main__':

    dir = '../data/'
    file = 'samples.json'

    attrs = [u'author', u'publisher', u'title', u'year', u'pages']

    resfile = 'check.json'

    with open(dir + file, 'r') as datafile:
        samples = json.load(datafile)

    res = []
    i = 0
    for sample in samples[:100]:
        i += 1
        # print sample[u'name']
        attrs_in_post = {}
        for attr in attrs:
            if attr in sample[u'attr']:
                attrs_in_post[attr] = find_attr(sample[u'name'], sample[u'attr'][attr])
            else:
                attrs_in_post[attr] = []
            # print sample[u'attr'][attr]
            # print '\t', attrs_in_post[attr]

        tokens = sample[u'name'].split(' ')

        post_attrs = []
        for tok, ind in zip(tokens, range(len(tokens))):
            for attr in attrs_in_post:
                if ind in attrs_in_post[attr]:
                    post_attrs.append((tok, attr))
                    break
            else:
                post_attrs.append((tok, 'junk'))
            # print post_attrs[-1]
        res.append((sample[u'name'], post_attrs))
        print str(i) + '/' + str(len(samples))

    with open(dir + resfile, 'w') as output:
        json.dump(res, output)

    print 'Yay!'
