#!./env python

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.corpus.reader.wordnet import WordNetError
import string
import warnings
from rules.category import surrouding_dict, person_dict

### text processing
class LemmaTokenizer(object):
    def __init__(self):
        self.tokenize = word_tokenize
        self.pos_tagger = pos_tag
        self.lemma = WordNetLemmatizer()
        # later
        self.corrector = lambda x: x.lower() # SpellCorrector()
        # todo
        # to deal with abbreviations better, like it's can't

        self.stopwords = stopwords.words('english')
        self.punctuation = string.punctuation

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
            ### wn.morphy can also do this job
            ### actually lemmatize calls morphy
            ### rule-based suffix detachment. Eg. corpora -> corpus
            # lemma = wn.morphy(self.corrector(token), tag)
            # return lemma
            return self.synsetting(lemma, tag)

        # remove stopwords
        if token in self.stopwords:
            return None

        # remove punctuation
        if token in self.punctuation:
            return None

        return self.synsetting(token)

    def __filter(self, tokens):
        return [t for t in tokens if t]

    def __call__(self, sentence):
        # print(word_tokenize(sentence))
        # print(pos_tag(word_tokenize(sentence)))
        return self.__filter([self.lemmatize(t, tag) for t, tag in self.pos_tagger(self.tokenize(sentence))])
        #
        # return self.wsd(self.__filter([self.lemmatize(t, tag) for t, tag in pos_tag(word_tokenize(sentence))]), sentence)


### joint text and keywords processing

def relaxedSimi(syn1, syn2):
    """
    Compute similarity between two synsets
    """
    try:
        return wn.lch_similarity(syn1, syn2) or 0
    except WordNetError:
        return 0

def wrapRelaxedSimi(t1, t2):
    if t1 is None or t2 is None:
        return 0
    return relaxedSimi(wn.synset(t1), wn.synset(t2))

def maxSimi(synset, keyword):
    """
    Given a synset, compute its similarity with a keyword (plain english)
        By considering the maximum of its similarities with all the synsets of the keyword
    """
    if keyword is None:
        return 0
    return max([relaxedSimi(synset, s) for s in wn.synsets(keyword)])

def maxSentSimi(sent, keyword):
    """
    Given a sentence of synset names, compute its similarity with a keyword (plain english)
    """
    return max([maxSimi(wn.synset(t), keyword) for t in sent])

def keywordSimi(sentence, keywords):
    """
    Given a sentence of synset names, compute its similarity with each category keywords
    """
    return [maxSentSimi(sentence, k) for k in keywords]

def sentSimi(sent, keyword, vocab):
    """
    Given a vocab, compute the similarity of each token in it with a keyword
        if it is included in the sentence
    """
    # return [maxSimi(wn.synset(t), keyword) if t in sent else 0 for t in vocab]
    return [wrapRelaxedSimi(t, keyword) if t in sent else 0 for t in vocab]

