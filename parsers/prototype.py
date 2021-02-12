#  encoders/protoype.py  - reconjugator prototype encoder for training data generation and input encoding
#
#  Copyright © Mirinae Corp., John Wainwright 2020
#

import re
from utilities.namespace import NameSpace as NS

class VerbPhraseParser(object):
    "extracts the verb phrases in given pos-list"

    dedupWildcard = re.compile(r'(\*\;)+')
    verbTags = { 'VV', 'VA', 'VCP', 'VCN', 'VNOM', 'VVD', 'VHV', 'VAD', 'VHA' }

    def __init__(self, options):
        self.options = NS.from_dict(options)
        self.allConjugations = set()
        self.allTenses = set()

    def extractPhrase(self, mappedPosList, sourceText):
        "extracts final verb phrase in given pos-list"
        # for now, the phrase-structure parsings are not present, so heuristic is to run backwards over
        # the pattern-mapped morpheme list with a little FSM, looking for verb-phrase bounds based on POS tags.
        # Perhaps, for now, only working with the last, or main predicating verb-phrase in the sentence

        # 식사:NNG;  ~ 시키:VV;어:EC;들:VX;시:EP;ㄹ까요:SEF;.:SF;
        # 나:NP;는:TOP;자전거:NNG;를:JKO; ~  타:VV;ㄹ 수 있:VMOD;다:SEF;.:SF;
        # 은:TOP; ~ 아니:VCN;ㅂ니다:SEF;.:SF;
        # DDH:SL;는:TOP;빨리:MAG;답변:NNG;받:VV;도록:CCF;이야기:NNG;  ~  하:VV;여보:AUX;겠:TNS;습니다:SEF;.:SF;

        form = []
        conjugation = honorific = ''
        tense = 'present'
        endMp = verb = None
        formTag = formPattern = formString = formPosString = None
        for mp in reversed(mappedPosList):
            if mp.tag in { 'SF', }:
                continue
            if endMp is None:
                endMp = mp
            # switch on tag
            if mp.tag in { 'SEF', }:  # sentence-ending form => main conjugation form
                conjugation = mp.meaning.lower()
                form.append('*')
            elif mp.tag in { 'TNS', }:  # sentence-ending form => main conjugation form
                tense = mp.meaning.lower().replace(' tense', '')
                form.append('*')
            elif mp.tag in { 'EP' }:  # tense/honorific suffix head, decode specific phonemes
                if mp.phoneme in { '시', '으시' }:
                    honorific = 'honorific'
                elif mp.phoneme in { '았', '었', '였' }:
                    tense = 'past'
                elif mp.phoneme in { '겠' }:
                    tense = 'assertive'
                elif mp.phoneme in { '았었', '었었', '였었' }:
                    tense = 'past perfect'
                form.append('*')
            elif mp.tag in { 'VX' }:
                if mp.index > 0 and mappedPosList[mp.index-1].tag != 'EC' or not any (p.tag in self.verbTags for p in mappedPosList):
                    # aux verb used as predicate verb
                    verb = mp
                    form.append(mp.morph)
                    break
                else:
                    form.append(mp.morph)
            elif mp.tag in self.verbTags:  # ending predicate verb, terminate scan
                verb = mp
                form.append(mp.morph)
                break
            else:
                # verb affix ending-form (eg aux verb), record it on way to verb
                form.append(mp.morph)

        if verb:
            # gather stats
            self.allTenses.add(tense)
            self.allConjugations.add(conjugation)
            # parsed final verb-phrase, construct conjugation form tag & wild-card pattern
            formTag = ', '.join(f for f in (honorific, tense, conjugation) if f != '')
            #
            # in endingForm mode, trim prefix off up to last morpheme prior to a conjugating morpheme
            #   as it will determine conjugation forms that follow
            form.reverse()
            if self.options.phraseForm == 'endingForm':
                for i, m in enumerate(form):
                    if i < len(form)-1 and form[i+1] == '*':
                        form = form[i:]
                        break
            #
            formPattern = ';' + ';'.join(form) + ';'
            # compact runs of conjugating morph wild-cards
            startMorphIndex = -len(form)-1
            formPattern = self.dedupWildcard.sub('*;', formPattern)
            formString = '~ ' + sourceText[mappedPosList[startMorphIndex].sourceSpan[0]:endMp.sourceSpan[1]]
            formPosString = ';' + ';'.join(mp.morph for mp in mappedPosList[startMorphIndex:-1]) + ';'
        #
        return formTag, formPattern, formString, formPosString

    def dumpStats(self):
        "dump collected stats"
        print(f'\nTraining data stats\n\n{len(self.allTenses)} Tenses:\n')
        for t in sorted(self.allTenses):
            print('  ', t)
        print(f'\n{len(self.allConjugations)} Conjugations:')
        for c in sorted(self.allConjugations):
            print('  ', c)
