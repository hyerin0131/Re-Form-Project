#  training/data_sources/analyzed_file.py  - corpus data in the form of an already-analyzed corpus in JSON records form
#
#  Copyright © Mirinae Corp., John Wainwright 2020
#
from _collections import defaultdict
from pprint import pprint
import codecs, json, os, sys, glob

from training.data_sources.extractor import Extractor
from utilities.namespace import NameSpace as NS

class DataSource(object):
    "base class for all analysis-annotated data-sources"

    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class File(DataSource):
    "a simple file of JSON structure records in standard Mirinae analysis format"

    def __init__(self, options):
        self.options = NS.from_dict(options)
        self.files = []
        self.extractor = Extractor(self, self.options)

    def __enter__(self):
        "establish 'with' context"
        super().__enter__()
        # self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        "clean-up 'with' context"
        self.close()
        return super().__exit__(exc_type, exc_value, traceback)

    def open(self):
        "open data source(s)"
        self.fileNames = glob.glob(self.options.sourceFiles)
        self.files = map(open, self.fileNames)
#         ... codecs.open(filename, encoding='cp949')
        return self

    def close(self):
        "close the data source(s)"
        for f in self.files:
            f.close()

    def records(self):
        "iterator over source records.  Returns projection specified in ctor options"
        for i, f in enumerate(self.files):
            print('=== processing ', self.fileNames[i])
            for line in f:
                yield self.extractor.extract(json.loads(line))
