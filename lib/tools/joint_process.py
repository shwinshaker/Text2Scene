#!./env python
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError

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
    try:
        return relaxedSimi(wn.synset(t1), wn.synset(t2))
    except WordNetError:
        return 0

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


