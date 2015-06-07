import json
from os import listdir
from copy import deepcopy


class PaperLinker():
    def __init__(self, filename, redirect_table):
        with open(redirect_table, 'r') as rtable:
            self.redirect_table = json.load(rtable)
        with open(filename, 'r') as file:
            self.data = json.load(file)
        self.datapath = []
        datadir = '../getpapers/data/papers/'
        self.datapath.append(datadir + "iter1/")
        self.datapath.append(datadir + "iter2/")
        self.datapath.append(datadir + "iter3/")
        self.datapath.append(datadir + "iter4/")
        self.datapath.append(datadir + "iter5/")
        self.datapath.append(datadir + "iter6/")
        self.datapath.append(datadir + "iter7/")

    def link(self):
        counter = 0
        papers = {}
        # link papers to their metadata
        for paper in self.data:
            counter += 1
            index = paper["pdf"].split('?')[1].split('&')[0]
            pdf = index + ".pdf"
            for path in self.datapath:
                if pdf in listdir(path):
                    papers[index] = {}
                    papers[index]["info"] = paper["info"]
                    papers[index]["pdf"] = path + pdf
                    papers[index]["refs"] = paper["refs"]
                    break
            print counter, len(self.data)
        self.data = papers
        # remove non-present references
        for paper in self.data:
            refs = []
            # convert cid into doi (if cid is in redirect table)
            for ref in self.data[paper]["refs"]:
                if ref in self.redirect_table:
                    refs.append(self.redirect_table[ref])
            self.data[paper]['refs'] = refs
            refs = deepcopy(self.data[paper]['refs'])
            # remove references not presented in the self.data
            for ind in xrange(len(self.data[paper]["refs"])):
                if self.data[paper]["refs"][ind] not in self.data:
                    refs.remove(self.data[paper]["refs"][ind])
            self.data[paper]["refs"] = refs
        print len(self.data.keys())
        return self

    def save(self, filename):
        with open(filename, "wt") as file:
            json.dump(self.data, file)
        return self


if __name__ == "__main__":
    datadir = "data/"
    filename = "papers.json"
    redirect = "rtable.json"
    plnk = PaperLinker(datadir + filename, datadir + redirect)
    plnk.link()
    output = "linked_papers.json"
    plnk.save(datadir + output)
