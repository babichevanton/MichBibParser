import sys
from os.path import exists
from time import time
import json
from data import DataStore, Post
from bsl import BlockingSchemeLearner
from extractor import PostExplorer


if __name__ == "__main__":
    datadir = "../data/"

    # itemsfile = 'samples.json'
    # postsfile = 'new_check.json'
    postsfile = sys.argv[1]
    itemsfile = sys.argv[2]
    first = int(sys.argv[3])
    last = int(sys.argv[4])
    resultfile = sys.argv[5]

    storebase_size = 10000       # number of elements in dataset
    RS_size = 10000              # number of elements in Reference Set
    SVMtrain_size = 10000        # number of SVM train items
    multiSVMtrain_size = 10000   # number of Multi-ClassSVM train items
    numofattrs = 5              # number of checking attributes

    with open(datadir + postsfile, "r") as pfile:
        check_data = json.load(pfile)
    posts = [post[0].strip() for post in check_data]

    store = DataStore()
    store.init_base(datadir + itemsfile, storebase_size)

    if RS_size > len(store.get_base()):
        size = len(store.get_base())
    else:
        size = RS_size

    bsl = BlockingSchemeLearner(store, 1, size)

    pexpl = PostExplorer(bsl.get_rs(),
                         store,
                         numofattrs,
                         datadir + "SVMmodel.model",
                         SVMtrain_size,
                         datadir + "MultiSVMmodel.model",
                         multiSVMtrain_size)

    i = 0
    for text in posts[first:last]:
        i += 1
        tm = time()
        post = Post(text)

        # rule = bsl.sequential_covering(post)

        # cands = bsl.get_candidates(rule)
        cands = bsl.get_rs()

        schema = pexpl.schema_predict(post, cands)

        post.print_cont()
        for attr_name in schema:
            print "    ", attr_name, schema[attr_name]

        attrs = pexpl.attrs_predict(post, schema)

        result = pexpl.results(post, attrs, schema)

        if not exists(datadir + resultfile):
            with open(datadir + resultfile, 'w') as output:
                json.dump({}, output)
        with open(datadir + resultfile, "r") as input:
            data = json.load(input)
        data[text] = {'schema': schema, 'attrs': result}
        with open(datadir + resultfile, "w") as output:
            json.dump(data, output)

        process_time = time() - tm
        print str(i) + '/' + str(len(posts)), process_time
