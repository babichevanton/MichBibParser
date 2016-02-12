#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from distance import jaccard
from jellyfish import levenshtein_distance as levenshtein
from jellyfish import jaro_winkler
from jellyfish import porter_stem


def jac_dist(str1, str2):
    return jaccard(str1.split(u' '), str2.split(u' '))


def lev_dist(str1, str2):
    return levenshtein(str1, str2)


def jw_dist(str1, str2):
    return 1.0 - jaro_winkler(str1, str2)


def sw_dist(s1,s2):
    """String edit distance, keeping trace of best alignment"""
    len1 = len(s1) # vertically
    len2 = len(s2) # horizontally
    # Allocate tables
    table = [None]*(len2+1)
    for i in range(len2+1): table[i] = [0]*(len1+1)
    trace = [None]*(len2+1)
    for i in range(len2+1): trace[i] = [None]*(len1+1)
    # initialize table
    for i in range(1, len2+1): table[i][0] = i
    for i in range(1, len1+1): table[0][i] = i
    # in the trace table, 0=subst, 1=insert, 2=delete
    for i in range(1,len2+1): trace[i][0] = 1
    for j in range(1,len1+1): trace[0][j] = 2

    def argmin(*a):
        """Return two arguments: first the smallest value, second its offset"""
        min = sys.maxint; arg = -1; i = 0
        for x in a:
            if (x < min):
                min = x; arg = i
            i += 1
        return (min,arg)

    # Do dynamic programming
    for i in range(1,len2+1):
        for j in range(1,len1+1):
            if s1[j-1] == s2[i-1]:
                d = 0
            else:
                d = 1
            # if true, the integer value of the first clause in the "or" is 1
            table[i][j],trace[i][j] = argmin(table[i-1][j-1] + d,
                                             table[i-1][j]+1,
                                             table[i][j-1]+1)

    del argmin
    return table[len2][len1]


def snd_dist(str1, str2):
    def soundex(name, len=5):
        """ soundex module conforming to Knuth's algorithm
            implementation 2000-12-24 by Gregory Jorgensen
            public domain
        """

        # digits holds the soundex values for the alphabet
        digits = '01230120022455012623010202'
        sndx = ''
        fc = ''

        # translate alpha chars in name to soundex digits
        for c in name.upper():
            if c.isalpha():
                if not fc: fc = c   # remember first letter
                d = digits[ord(c)-ord('A')]
                # duplicate consecutive soundex digits are skipped
                if not sndx or (d != sndx[-1]):
                    sndx += d

        # replace first digit with first alpha character
        sndx = fc + sndx[1:]

        # remove all 0s from the soundex code
        sndx = sndx.replace('0','')

        # return soundex code padded to len characters
        return (sndx + (len * '0'))[:len]

    sndstr1 = u' '.join([soundex(tok) for tok in str1.split(u' ')])
    sndstr2 = u' '.join([soundex(tok) for tok in str2.split(u' ')])
    res = lev_dist(sndstr1, sndstr2)
    del soundex
    return res


def ps_dist(str1, str2):
    tokstr1 = u' '.join([porter_stem(tok) for tok in str1.split(u' ')])
    tokstr2 = u' '.join([porter_stem(tok) for tok in str2.split(u' ')])
    return lev_dist(tokstr1, tokstr2)


if __name__ == '__main__':
    # str1 = u'Если б я имел коня, это был бы номер'
    # str2 = u'Если б конь имел меня, я б, наверно, помер'
    str1 = u'A long ago, in a galaxy far far away'
    str2 = u'A long ago, in a galaxy far far away'
    # str2 = u'It\' been a long time when i was a child'

    print str1
    print str2
    print ''
    print 'Jaccard distance is', jac_dist(str1, str2)
    print 'Levenshtein distance is', lev_dist(str1, str2)
    print 'Smith-Waterman distance is', sw_dist(str1, str2)
    print 'Jaro-Winkler distance is', jw_dist(str1, str2)
    print 'Soundex distance is', snd_dist(str1, str2)
    print 'Porter Stemmer distance is', ps_dist(str1, str2)
