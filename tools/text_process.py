#!./env python

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords

import spacy # use spacy now for sophicated tagging
from spacy.lemmatizer import Lemmatizer
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES

import string
import warnings

from tools.instance import Node

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
    def __init__(self, path='google-10000-english-usa-no-swears.txt'):
        with open(path, 'r') as f:
            word_freq = [w.strip('\n') for w in f]
        self.freq_dict = dict([(w, i) for i, w in enumerate(word_freq)])

        self.nlp = spacy.load("en_core_web_md")
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


class SpacyLemmaTokenizer:

    """
    rewrite this... spacy is too damned simple
    """
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.lemmatizer = Lemmatizer(LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES)

    def penn_to_lemma(self, tag):
        """
        Convert output of pos tagger to wordnet tags
        Only nouns, verbs, adjectives and adverbs will be kept.
        """
        if tag.startswith('J'):
            return 'ADJ'
        elif tag.startswith('N'):
            return 'NOUN'
        elif tag.startswith('R'):
            return 'ADV'
        elif tag.startswith('V'):
            return 'VERB'
        return None

    def le_to_wn(self, tag):
        return tag
        dic = {'ADJ': wn.ADJ,
               'NOUN': wn.NOUN,
               'ADV': wn.ADV,
               'VERB': wn.VERB}
        return dic[tag]

    def lemmatize(self, token, tag):
        lemma_tag = self.penn_to_lemma(tag)
        if lemma_tag is None: return Node(token, tag) #Node(token, 'UNK')
        return Node(self.lemmatizer(token, lemma_tag)[0], self.le_to_wn(lemma_tag))

    def __filter(self, token):
        return token.is_stop or token.is_punct

    def __call__(self, sentence):
        doc = self.nlp(sentence.strip('\n'))
        return [self.lemmatize(token.text, token.tag_) for token in doc if not self.__filter(token)]


### text processing
class LemmaTokenizer(object):
    def __init__(self):
        self.tokenize = word_tokenize
        self.pos_tagger = pos_tag
        self.lemma = WordNetLemmatizer()
        # later
        # self.corrector = lambda x: x.lower() # SpellCorrector()
        # todo
        # to deal with abbreviations better, like it's can't

        self.stopwords = stopwords.words('english')
        self.punctuation = string.punctuation


    def corrector(self, token):
        # todo
        return token.lower()

    def penn_to_wn(self, tag):
        """
        Convert output of pos tagger to wordnet tags
        Only nouns, verbs, adjectives and adverbs will be kept.
        """
        if tag.startswith('J'):
            return wn.ADJ
        elif tag.startswith('N'):
            return wn.NOUN
        elif tag.startswith('R'):
            return wn.ADV
        elif tag.startswith('V'):
            return wn.VERB
        return None

    def synsetting(self, lemma, tag=None):
        # synset only disambiguate POS. Eg. noun and verb
        synsets = wn.synsets(lemma, tag)
        if len(synsets) >= 1:
            return synsets[0].name()
        warnings.warn('%s with tag %s does not belong to any synsets.' % (lemma, tag))
        return None

    def wsd(self, sent, sentence):
        # word sense disambiguation is unstable
        return [lesk(self.tokenize(sentence), lemma) for lemma in sent]

    def lemmatize(self, token, tag):
        token = self.corrector(token)
        tag = self.penn_to_wn(tag)

        # if nouns, verbs, adjs, advs, lemmatize
        if tag: # N,V,ADJ,ADV
            lemma = self.lemma.lemmatize(token, tag)
            # remove stopwords
            # Eg. remove 'be'
            if lemma in self.stopwords:
                return None
            ### wn.morphy can also do this job
            ### actually lemmatize calls morphy
            ### rule-based suffix detachment. Eg. corpora -> corpus
            # lemma = wn.morphy(self.corrector(token), tag)
            return Node(lemma, tag)
            # return self.synsetting(lemma, tag)

        # remove stopwords
        if token in self.stopwords:
            return None

        # remove punctuation
        if token in self.punctuation:
            return None

        return Node(token, 'UNK') #self.synsetting(token)

    def __filter(self, tokens):
        return [t for t in tokens if t]

    def __call__(self, sentence):
        # print(word_tokenize(sentence))
        # print(pos_tag(word_tokenize(sentence)))
        return self.__filter([self.lemmatize(t, tag) for t, tag in self.pos_tagger(self.tokenize(sentence))])
        #
        # return self.wsd(self.__filter([self.lemmatize(t, tag) for t, tag in pos_tag(word_tokenize(sentence))]), sentence)
