#!./env python

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
import string
import warnings

from tools.instance import Node

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

