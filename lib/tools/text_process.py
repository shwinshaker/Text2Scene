#!./env python

import spacy
from spacy.lemmatizer import Lemmatizer
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES

import string
import warnings

from .instance import Node

import os
from spacy.tokens import Doc, Span, Token
from hunspell import HunSpell

DEFAULT_DICTIONARY_PATHS = {
    'darwin': '/Users/dongjustin/Library/Spelling/en_US',
    'linux': '/usr/share/hunspell',
}

class spaCyHunSpell(object):

    name = 'hunspell'

    def __init__(self, nlp, path):
        """
        why would we needs nlp?
        """
        if path in DEFAULT_DICTIONARY_PATHS:
            default_path = DEFAULT_DICTIONARY_PATHS[path]
            dic_path, aff_path = (
                os.path.join(default_path, 'en_US.dic'),
                os.path.join(default_path, 'en_US.aff'),
            )
            print(dic_path, aff_path)
        else:
            assert len(path) == 2, 'Include two paths: dic_path and aff_path'
            dic_path, aff_path = path

        self.hobj = HunSpell(dic_path, aff_path)

        Token.set_extension('hunspell_spell', default=None, force=True)
        Token.set_extension('hunspell_suggest', getter=self.get_suggestion, force=True)

    def __call__(self, doc):
        for token in doc:
            token._.hunspell_spell = self.hobj.spell(token.text)
        return doc

    def get_suggestion(self, token):
        # TODO: include a lower option?
        # TODO: include suggestion numbers?
        # TODO: include stemmer?
        return self.hobj.suggest(token.text)

class Check:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def __call__(self, sentence):
        doc = self.nlp(sentence)
        errors = [] #{'non-ascii': []}
        for t in doc:
            if not t.is_ascii:
                # errors['non-ascii'].append(t)
                errors.append(t)
        return errors

class Spell:
    def __init__(self, path='extras/google-10000-english-usa-no-swears.txt'):
        print('Open extras/google-10000-english-usa-no-swears.txt')
        with open(path, 'r') as f:
            word_freq = [w.strip('\n') for w in f]
        self.freq_dict = dict([(w, i) for i, w in enumerate(word_freq)])
        print('done.')

        print('Loading en_core_web_sm..')
        self.nlp = spacy.load("en_core_web_sm")
        print('Loaded.')

        from sys import platform
        print('Running on %s' % platform)
        hunspell = spaCyHunSpell(self.nlp, platform)
        self.nlp.add_pipe(hunspell)

    def __call__(self, sentence):
        doc = self.nlp(sentence)
        suggests = {}
        text = []
        for t in doc:
            # digits is spelled in hun
            # puncts is not spelled in hun
            # what about others?
            if t.is_punct: continue
            # if t.is_oov: # unexpected out-of-vocabulary words
            if t._.hunspell_spell == False:
                suggests[t] = sorted(filter(lambda w: w in self.freq_dict, t._.hunspell_suggest), key=lambda w: self.freq_dict[w])[:2]
        return suggests
        # for t in suggests:
        #     if suggests[t]:
        #         text.append('Out-of-vocabulary word "%s": Did you mean "%s"?' % (t, ', '.join(suggests[t])))
        #     else:
        #         text.append('Out-of-vocabulary word "%s"' % t)

        # return text


class SimpleLemmaTokenizer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe(self.__filter, last=True)
        self.nlp.add_pipe(self.__to_node, last=True)

    def __filter(self, doc):
        return [t for t in doc if not t.is_stop and not t.is_punct]
        # return [t for t in doc if not t.is_stop]

    def __to_node(self, doc):
        return [Node(t.lemma_, t.pos_) for t in doc]

    def __call__(self, sentence):
        return self.nlp(sentence.strip('\n'))

#################################
#################################

