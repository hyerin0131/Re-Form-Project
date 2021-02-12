#  training/generators/protoype.py  - reconjugator prototype training-file generator
#
#  Copyright © Mirinae Corp., John Wainwright 2020
#

import sys, os, json, pickle
from pprint import pprint
from collections import defaultdict
from itertools import permutations

# ensure main source route is on python path
sys.path.insert(0, os.path.dirname(__file__) + "/../..")

from training.data_sources.analyzed_file import File
from parsers.prototype import VerbPhraseParser
from utilities.namespace import NameSpace as NS

class Generator(object):
    "implements original prototype Reconjugator training-data generator"
    # using the pre-analyzed data-source capabilities of the pipeline API

    def __init__(self, options={}):
        self.options = NS.from_dict(options)
        self.forms = defaultdict(set)

    def extractPhraseSets(self, source, parser):
        "process given Mirinae annotated data-source, extracting related verb-phrase sets"
        #
        with source.open() as s:
            counter = 1
            for rec in s.records():
                if len(rec.analysis.sentence.mappedPosList) > 2:
                    formTag, formPattern, formString, formPosString = parser.extractPhrase(rec.analysis.sentence.mappedPosList, rec.analysis.sentence.sourceText)
                    #
                    if not formTag:
                        #  print("** can't parse ", rec.analysis.sentence.sourceText)
                        pass
                    else:
                        self.forms[formPattern].add((formString.strip(), formTag.strip(), formPosString))
                        if counter % 5000 == 0:
                            print(counter)
                        counter += 1

        #
        # dump raw training instances
        with open(self.options.verbPhrasesFileName, 'w') as odf:
            for formPattern, instances in self.forms.items():
                data = dict(formPattern=formPattern, instances=list(instances))
                json.dump(data, odf, ensure_ascii=False); odf.write('\n')

    def buildRawTrainingPairs(self):
        "loads phrase-set file, build permutted training-pairs; outputs to rawTrainingPair file"
        with open(self.options.verbPhrasesFileName) as vpf:
            with open(self.options.rawTrainingsPairFileName, 'w') as rtpf:
                counter = 0
                for line in vpf:
                    data = json.loads(line)
                    instances = data['instances']
                    if len(instances) > 1:
                        # only makes sense to permute if > 1 conjugation instance
                        if self.options.v2Pairs:
                            data['rawPairs'] = [(((p[0][0], p[0][2]), p[1][1]), (p[1][0], p[1][2])) for p in permutations(instances, 2)]
                        else:
                            data['rawPairs'] = [(p[0], p[1]) for p in permutations(instances, 2)]
                        json.dump(data, rtpf, ensure_ascii=False); rtpf.write('\n')
                        #
                        counter += 1
                        if counter % 100 == 0:
                            print(counter)


if __name__ == "__main__":

    sourceOptions = {
        'sourceFiles': '/Users/jwainwright/Downloads/AI-hub_data/*.json',
        'projection': ['analysis.sentence.mappedPosList', 'analysis.sentence.sourceText', 'analysis.sentence.mappedPosString']
    }
    source = File(sourceOptions)

    # with source.open() as s:
    #     counter = 1
    #     with open('samples.txt', 'w') as outs:
    #         for rec in s.records():
    #             outstr = ' '.join(mp.morph + ';' for mp in rec.analysis.sentence.mappedPosList)
    #             outs.write(outstr); outs.write('\n')
    #             counter += 1
    #             if counter > 1000:
    #                 break
    #
    #
    #
    generatorOptions = {
        'verbPhrasesFileName': '/Users/jwainwright/Downloads/AI-hub_data/AI-hub+KAIST-60K-verb-phrases.json',
        'v2Pairs': False,
        'rawTrainingsPairFileName': '/Users/jwainwright/Downloads/AI-hub_data/AI-hub+KAIST-60K-raw-training-pairs-v1.json',
    }
    gen = Generator(generatorOptions)
    #
    parserOptions = {
        'phraseForm': 'verbPhrase',   # 'endingForm'
    }
    phraseParser = VerbPhraseParser(parserOptions)
    #
    #gen.extractPhraseSets(source, phraseParser)
    gen.buildRawTrainingPairs()

    # dump stats
    phraseParser.dumpStats()


