import os
import re
import json


from scrapy import Selector
import bibtexparser


class Paper:
    def __init__(self):
        self.info = {}
        self.refs = []
        self.pdf = ""

    def to_json(self):
        ser_paper = {}
        ser_paper["pdf"] = self.pdf
        ser_paper["info"] = self.info
        ser_paper["refs"] = self.refs
        return ser_paper

    def print_paper(self):
        print "pdf:  " + self.pdf
        print "info:"
        for item in self.info.items():
            print "  ", ": ".join(item)
        print "refs:"
        for ref in self.refs:
            print "  ", ref


class Extractor():
    def get_pdf(self, text):
        sel = Selector(text=text)
        pdf = sel.xpath('//div[@id="wrapper"]' +
                        '/div[@id="main"]' +
                        '/div[@id="viewHeader"]' +
                        '/div[@id="downloads"]' +
                        '/ul[@id="clinks"]' +
                        '/li/a[@title="View or Download this document as PDF"]/@href').extract()
        if len(pdf) == 0:
            return ""
        return "http://citeseerx.ist.psu.edu" + re.sub(";.*\?", "?", pdf[0])

    def get_info(self, text):
        sel = Selector(text=text)
        bibtex_str = sel.xpath('//div[@id="wrapper"]' +
                               '/div[@id="main"]' +
                               '/div[@id="viewContent"]' +
                               '/div[@id="viewContent-inner"]' +
                               '/div[@id="viewSidebar"]' +
                               '/div[@id="bibtex"]' +
                               '/p/text()').extract()
        bibtex_str =  "\n".join(bibtex_str)
        bib_database = bibtexparser.loads(bibtex_str)
        return bib_database.entries[0]

    def get_refs(self, text):
        sel = Selector(text=text)
        references = sel.xpath('//div[@id="wrapper"]' +
                               '/div[@id="main"]' +
                               '/div[@id="viewContent"]' +
                               '/div[@id="viewContent-inner"]' +
                               '/div[@id="citations"]' +
                               '/table[@class="refs"]' +
                               '/tr/td/a/@href').extract()
        references = [ref.split("?")[1] for ref in references if ref != ""]
        return references

    def get_refs_for_rt(self, text):
        sel = Selector(text=text)
        references = sel.xpath('//div[@id="wrapper"]' +
                               '/div[@id="main"]' +
                               '/div[@id="viewContent"]' +
                               '/div[@id="viewContent-inner"]' +
                               '/div[@id="citations"]' +
                               '/table[@class="refs"]' +
                               '/tr/td/a/@href').extract()
        references = filter(lambda x: x != '', references)
        references = list(set(['http://citeseerx.ist.psu.edu'+ ref for ref in filter(lambda x: x.startswith('/viewdoc'), references)]))
        return references

    def extract(self, filename):
        with open(filename, "rb") as f:
            text = f.read()
        paper = Paper()
        paper.pdf = self.get_pdf(text)
        paper.info = self.get_info(text)
        paper.refs = self.get_refs(text)
        return paper

    def extract_references(self, filename):
        with open(filename, "rb") as f:
            text = f.read()
        return self.get_refs_for_rt(text)


if __name__ == "__main__":
    dir = "../getpapers/data/pages/"

    files = filter(lambda x: x.endswith(".html"), os.listdir(dir))

    papers_file = "data/papers.json"
    # references = 'data/references.json'

    ex = Extractor()

    papers = []
    # links = []
    i = 0
    for filename in files:
        i += 1
        papers.append(ex.extract(dir + filename).to_json())
        # links.extend(ex.extract_references(dir + filename))
        print i, len(files)

    papers = filter(lambda x: x['pdf'] != '', papers)

    with open(papers_file, "wt") as output:
        json.dump(papers, output)
    # with open(references, "wt") as output:
    #     json.dump(links, output)
