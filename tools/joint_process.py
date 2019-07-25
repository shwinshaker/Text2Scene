#!./env python
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError
from scipy import sparse
from tools.common import flattenNested

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
    **Deprecated**
    """
    return max([maxSimi(wn.synset(t), keyword) for t in sent])

def keywordSimi(sentence, keywords):
    """
    Given a sentence of synset names, compute its similarity with each category keywords
    **Deprecated**
    """
    return [maxSentSimi(sentence, k) for k in keywords]

def sentSimi(sent, keyword, vocab):
    """
    Given a vocab, compute the similarity of each token in it with a keyword
        if it is included in the sentence
    """
    # return [maxSimi(wn.synset(t), keyword) if t in sent else 0 for t in vocab]
    return [wrapRelaxedSimi(t, keyword) if t in sent else 0 for t in vocab]


class SimiEncoder():
    def __init__(self, img_encoder, txt_encoder):
        self.img_encoder = img_encoder
        self.txt_encoder = txt_encoder

        # set features
        ### be extremely careful here for the order of feature names
        self.features_ = []
        self.features_.extend(['_S_%s_%s_' % (k, t) for k in img_encoder.srd_categ for t in txt_encoder.vocab_])
        self.features_.extend(['_P_%s_%s_' % (k, t) for k in img_encoder.prs_categ for t in txt_encoder.vocab_])

    def encode(self, layer_names, sentence):
        assert(isinstance(layer_names, list))
        assert(isinstance(layer_names[0], str))
        assert(layer_names[0].startswith('A'))
        assert(isinstance(sentence, str))

        keywords = self.img_encoder.layer2keyword(layer_names)
        tokens = self.txt_encoder.tokenizer(sentence)
        return flattenNested([sentSimi(tokens, k, self.txt_encoder.vocab_) if k in keywords else sentSimi(tokens, None, self.txt_encoder.vocab_) for k in self.img_encoder.category_])




