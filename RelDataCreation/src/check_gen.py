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
    similarity = (0, maxint)
    window_size = len(attr.split(' '))

    # preprocessing
    attr = filter(lambda x: x not in punctuation or x is '-', attr).upper().split(' ')
    tokens = filter(lambda x: x not in punctuation or x is '-', post).upper().split(' ')
    # tokens = zip(tokens, range(len(tokens)))

    # matching
    for i in range(1, window_size + 1)[-1::-1]:
        for j in xrange(len(tokens) - i + 1):
            cand = ''
            cand_ind = []
            for k in xrange(i):
                cand += tokens[j + k] + ' '
                cand_ind.append(j + k)
            cand = cand.strip()
            # Levenshtein
            #TODO paste something more complicated
            tok_prefixes = 0
            attr_tokens = map(lambda x: [x, True], attr)
            cand_tokens = cand.split(' ')
            cand_tokens.sort(key=len, reverse=True)
            cand_tokens = map(lambda x: [x, True], cand_tokens)
            for attr_ind in xrange(len(attr_tokens)):
                for tok_ind in xrange(len(cand_tokens)):
                    # more length - first. Initials will be the last to match
                    if cand_tokens[tok_ind][1] and attr_tokens[attr_ind][1] and \
                            attr_tokens[attr_ind][0].startswith(cand_tokens[tok_ind][0]):
                        tok_prefixes += 1
                        cand_tokens[tok_ind][1] = False
                        attr_tokens[attr_ind][1] = False
                        break
            dist = levenshtein(unicode(cand), unicode(' '.join(attr)))
            if tok_prefixes > similarity[0] or (tok_prefixes == similarity[0] and dist < similarity[1]):
                similarity = (tok_prefixes, dist)
                result = cand_ind
                res_cand = cand
    res = zip(res_cand.split(), result)
    temp = copy(res)
    for tok in temp:
        if substr(' '.join(attr), tok[0]) < 0:
            res.remove(tok)
    return map(lambda x: x[1], res)


if __name__ == '__main__':

    dir = '../data/'
    file = 'samples_v2.json'

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
