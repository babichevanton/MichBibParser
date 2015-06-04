import sys
from data import DataStore, Post
from bsl import BlockingSchemeLearner
from extractor import PostExplorer


if __name__ == "__main__":
    datadir = "../data/"

    itemsfile = sys.argv[2]
    postsfile = sys.argv[1]

    storebase_size = 7000       # number of elements in dataset
    RS_size = 2000              # number of elements in Reference Set
    SVMtrain_size = 7000        # number of SVM train items
    multiSVMtrain_size = 7000   # number of Multi-ClassSVM train items
    numofattrs = 5              # number of checking attributes

    with open(datadir + postsfile, "rt") as pfile:
        posts = [post.strip() for post in pfile.readlines()]

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
                         multiSVMtrain_size,
                         datadir + "decode.pkl")

    for text in posts[:1]:
        post = Post(text)

        rule = bsl.sequential_covering(post)

        cands = bsl.get_candidates(rule)

        schema = pexpl.svm_predict(post, cands)

        post.print_cont()
        for attr_name in schema:
            print "    ", attr_name, schema[attr_name]

        attrs = pexpl.multisvm_predict(post, schema)

        pexpl.results(post, attrs, schema, datadir + "res.json")
