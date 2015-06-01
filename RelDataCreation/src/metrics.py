import sys
from jellyfish import porter_stem
from jellyfish import soundex


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


def argmin(*a):
    """Return two arguments: first the smallest value, second its offset"""
    min = sys.maxint; arg = -1; i = 0
    for x in a:
        if (x < min):
            min = x; arg = i
        i += 1
    return (min,arg)


def smith_waterman(s1,s2):
    "String edit distance, keeping trace of best alignment"
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
    return table[len2][len1]


if __name__ == "__main__":
    print smith_waterman("ACACACTA", "")
    # res = [porter_stem(word) for word in "goodbue my cruel world".split()]
    # for word in res:
    #     print word
