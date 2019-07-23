#!./env python
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError
from scipy import sparse
from tools.image_process import getNestedKey, getNestedKeyWithCode, name2code
from rules.category import person_dict, surrouding_dict
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


def getFeatureSimiWithCode(dic, sent, code=None):
    """
    Get the max similarity of a sentence with each keyword
        given the sub-category code
        **Deprecated**
    """
    keywords = []
    if code:
        keywords = getNestedKeyWithCode(dic, code)
    all_keywords = getNestedKey(dic)
    return [maxSentSimi(sent, k) if k in keywords else 0 for k in all_keywords]


def image2SimiFeature(layer_names, sentence):
    """
    Get the max similarity of a sentence with each keyword as joint feature
        **Deprecated**
    """
    assert(isinstance(layer_names, list))
    assert(isinstance(layer_names[0], str))
    assert(isinstance(sentence, list))
    assert(isinstance(sentence[0], str))

    features = []
    # sub-categories, keyword simi
    codes = [name2code(name) for name in layer_names]
    cat_codes = [code[0] for code in codes]
    for c, dic in zip([2, 3], [surrouding_dict, person_dict]):
        if c in cat_codes:
            subcode = codes[cat_codes.index(c)][1:]
        else:
            subcode = None
        features.append(getFeatureSimiWithCode(dic, sentence, subcode))

    return flattenNested(features)

def getCrossSimiWithCode(dic, sent, vocab, code=None):
    """
    Get the cross similarities between each category keyword and each word in the vocabulary, given the subcode
    """
    keywords = []
    if code:
        keywords = getNestedKeyWithCode(dic, code)
    all_keywords = getNestedKey(dic)
    return [sentSimi(sent, k, vocab) if k in keywords else sentSimi(sent, None, vocab) for k in all_keywords]

def getCrossSimi(layer_names, sentence, vocab):
    """
    Get the cross similarities between each category keyword and each word in the vocabulary as the joint features
    """
    assert(isinstance(layer_names, list))
    assert(isinstance(layer_names[0], str))
    assert(isinstance(sentence, list))
    assert(isinstance(sentence[0], str))

    features = []
    # sub-categories, keyword simi
    codes = [name2code(name) for name in layer_names]
    cat_codes = [code[0] for code in codes]
    for c, dic in zip([2, 3], [surrouding_dict, person_dict]):
        if c in cat_codes:
            subcode = codes[cat_codes.index(c)][1:]
        else:
            subcode = None
        features.append(sparse.csr_matrix(getCrossSimiWithCode(dic, sentence, vocab, subcode)))

    return sparse.vstack(features) # flattenNested(features)
