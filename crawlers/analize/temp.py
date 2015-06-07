import json


dir = 'data/'
name = 'check.json'
sfile = 'samples.json'

res = 'check.txt'

with open(dir + name, 'r') as input:
    samples = json.load(input)
with open(dir + sfile, 'r') as input:
    ss = json.load(input)

i = 0
for sample, s in zip(samples, ss):
    i += 1
    post = sample[0]
    print post
    post_attrs = map(lambda x: '\t' + x + '\n\t\t' + s[u'attr'][x], s[u'attr'])
    # for attr in post_attrs:
    #     print attr
    # output.writelines(post_attrs)
    attrs = map(lambda x: '\t' + x[0] + '\n\t\t' + x[1], sample[1])
    for attr in attrs:
        print attr
    # output.writelines(attrs)
    print i

print 'Yay!'
