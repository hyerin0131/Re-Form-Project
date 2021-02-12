#  training/data_sources/analyzed_file.py  - corpus data in the form of an already-analyzed corpus in JSON records form
#
#  Copyright © Mirinae Corp., John Wainwright 2020
#

import base64, zlib, json

from utilities.namespace import NameSpace as NS

class Extractor(object):
    "tool to unpack & project requested sub-structures from annotated analysis"

    def __init__(self, source, options):
        self.source = source
        self.options = NS.from_dict(options)
        self.projection = self.options.projection

    def extract(self, data, projection=None):
        "unpack standard fields from the data record and extract under supplied or options-based projection spec"
        projection = projection or self.options.get('projection') or 'all'
        # default fields are 'text' and 'analysis'.  The analysis is in a special compact form, needs unpacking.
        data['analysis'] = self.unpackAnalysis(data['analysis'])
        data = NS.from_dict(data)
        if projection == 'all':
            result = data
        else:
            # project
            result = NS(auto_add_levels=True)
            for field in projection:
                result[field] = data[field]
        #
        return result

    def unpackAnalysis(self, packedAnalysis):
        "unpack packed analysis"
        ca = base64.b64decode(packedAnalysis)
        ja = zlib.decompress(ca)
        return json.loads(ja)


