#!./env python

from xml.dom.minidom import parse
import os
import numpy as np
import glob
import re
from itertools import count
from rules.category import person_dict, surrouding_dict
from tools.text_process import maxSentSimi, sentSimi
from scipy import sparse

### Get layer names give the .svg file
def getLayerNames(file):
    """
    Get the name of each layer in the image
        first check the id attribute of <svg>
        then check the id attribute of <g>s
    """
    doc = parse(file)
    svg_list = doc.getElementsByTagName('svg')
    assert(len(svg_list) == 1)
    svg = svg_list[0]
    # layers = [g for g in svg.childNodes \
    #           if g.nodeType == 1 and \
    #              g.tagName == 'g' and \
    #              g.hasAttribute('id')]
    layers = [g for g in doc.getElementsByTagName('g') \
              if g.nodeType == 1 and \
                 g.hasAttribute('id') and g.getAttribute('id').startswith('A')]

    ## todo - clean marks like _x3_  and find names subject to pattern
    ### like what we do in the following
    if layers:
        for layer in layers[1:]:
            assert(layer in layers[0].parentNode.childNodes), 'Ids not at the same level!'
        return [l.getAttribute('id') for l in layers]
    else:
        if svg.hasAttribute('id'):
            # if single layer case, id belongs to <svg>
            # todo - check there be at most 1 <g> on each level
            assert(len([g for g in svg.childNodes \
                          if g.nodeType == 1 and \
                             g.tagName == 'g']) <= 1)
            return [svg.getAttribute('id')]
        else:
            raise ValueError('No valid id name found!')

def cleanName(name):
    """
    remove irregular marks in adobe illustrator
    """
    return re.sub('_x?\d+_','',name)

def name2code(name):
    """
    input: A-1-2-3-4 or A1234
    output: [1,2,3,4]
    """
    name = cleanName(name)

    if re.match(r'^A(-\d)+$', name):
        return [int(d) for d in name.split('-')[1:]]
    elif re.match(r'^A\d+$', name):
        return [int(d) for d in list(name)[1:]]
    else:
        raise KeyError('%s fails to match with pattern!' % name)

def checkLayerNames(names):
    """
    Check if the names of layers we got make sense
    """

    if isinstance(names[0], str):
        cat_codes = [name2code(s)[0] for s in names]
    elif isinstance(names[0], int):
        cat_codes = names
    else:
        raise TypeError('Invalid input type!')

    # if background in, it must be the most bottom layer
    if 1 in cat_codes:
        assert(cat_codes.index(1) == 0), 'background should be the most bottom!'

    # if decoration in, it must be the most top or bottom layer
    if 4 in cat_codes:
        assert(cat_codes.index(4) == 0 or cat_codes.index(4) == len(cat_codes) - 1), 'decoration should be the most top or bottom!'

    ## one of surrounding or person should be in the scene
    assert(2 in cat_codes or 3 in cat_codes), 'Neither person nor surroundings are found in the scene!'

    # if only one layer, must be surrounding layer
    if len(cat_codes) == 1:
        assert(cat_codes[0] == 2), 'it must be the surrounding layer if there is only one layer'
    # else: ## not necessarily
    #     # if multiple layers, check the cat order
    #     # background 1 - surroundings 2 - person 3 - decoration 4
    #     for code1, code2 in zip(cat_codes[:-1], cat_codes[1:]):
    #         assert(code2 > code1), \
    #            'layer %s should not be below layer %s!' % (code2, code1)


### From layer name to image features
def getDepth(li):
    """
    Get the depth of a nested list
    """
    for level in count():
        if not li:
            return level
        li = [e for l in li if isinstance(l, list) for e in l]

def recurReplace(nested, id_list, value=1):
    """
    Replace an element in a nested list recursively
    """
    # number of indexes should be lower than the depth
    assert(len(id_list) <= getDepth(nested))

    # print(nested, '--', id_list)
    if len(id_list) > 1:
        recurReplace(nested[id_list[0]], id_list[1:])
    else:
        nested[id_list[0]] = value

def isPureList(l):
    """
    Check if a list is not a nested one
    """
    for e in l:
        if isinstance(e, list):
            return False
    return True

def code2indslist(code):
    """
    Turn a code into the reference indexes of a nested list
        Eg. [2,1,2,1] -> [0,1,0]
        the first number is the ident code of the layer type
    """
    return [d-1 for d in code[1:]]

def flattenNested(nested):
    """
    Flatten a nested list
        support two-level nested, with number mixed
        Eg. [3,[1,2,3],5,[2,4]]
    """
    flatten = []
    for l in nested:
        if isinstance(l, list):
            assert(isPureList(l))
            flatten.extend([e for e in l])
        else:
            flatten.append(l)
    return flatten


def extractLeaf(feat, depth, concat=[], level=0):
    """
    Extract the leaf lists in the same level in a nested list
    """
    level += 1
    # print('  ', level, depth, concat)
    for i, e in enumerate(feat):
        if isinstance(e, list):
            if isPureList(e):
                # lowest level only
                if level == depth - 1:
                    concat.extend(e)
                    feat[i] = sum(e)
            else:
                feat[i], concat = extractLeaf(e, depth, concat, level)
    return feat, concat


def oneHotStructEncode(feat):
    """
    Given the nested features,
        encode each category level into one-hot
    """
    concats = []
    while not isPureList(feat):
        feat, concat = extractLeaf(feat,
                                   getDepth(feat),
                                   concat=[],
                                   level=0)
        # print(feat, concat)
        concats.append(concat)
    concats.append(feat)
    return flattenNested(concats[::-1])

def getNestedKey(obj):
    """
    recursion wrapper
    """
    keys = []
    getNestedKey_(obj, keys=keys)
    return keys

def getNestedKey_(obj, keys=[]):
    """
    get all the keys in a nested dictionary
        todo - keys argument can be saved if use reference
    """
    if isinstance(obj, dict):
        for key in obj:
            keys.append(key)
            getNestedKey_(obj[key], keys)
    elif isinstance(obj, list):
        for key in obj:
            getNestedKey_(key, keys)
    elif isinstance(obj, str):
        keys.append(obj)
    else:
        raise KeyError

def getNestedKeyWithCode(obj, code):
    keys = []
    for c in code:
        if isinstance(obj, dict):
            key = list(obj.keys())[c - 1]
            keys.append(key)
            obj = obj[key]
        elif isinstance(obj, list):
            l = []
            for key in obj:
                if isinstance(key, str):
                    l.append(key)
                elif isinstance(key, dict):
                    l.extend(list(key.keys()))
                else:
                    raise TypeError('Invalid type other than str and dict')
            key = l[c - 1]
            keys.append(key)
            if key in obj:
                obj = key # should end here
            else:
                for obj_ in obj:
                    if isinstance(obj_, dict) and key in obj_.keys():
                        obj = obj_[key]
        else:
            raise TypeError('Invalid type other than str and dict. Could be incorrect query code!')
    return keys

def image2feature_old(layer_names):
    """
    One-hot encode the names of layers. Leaf one-hotting
    """

    features = []

    # number of layers
    features.append(len(layer_names))

    # convert to digit codes first
    codes = [name2code(name) for name in layer_names]

    # four layer type, binary
    feat_layer = [0] * 4
    for code in codes:
        feat_layer[code[0] - 1] = 1
    features.append(feat_layer)

    # sub-categories - one-hot for each level
    # get surrounding and person code, if any
    code_srd = None
    code_prs = None
    for code in codes:
        if code[0] == 1 or code[0] == 4:
            # background or decoration, no need to encode
            assert(len(code) == 1)
        elif code[0] == 2:
            # surrounding
            code_srd = code
        elif code[0] == 3:
            code_prs = code
        else:
            raise ValueError('Invalid layer type code!')

    # surrounding(2) template
    # feat = [[0,[0,0,0]],[0,[0,0,0],[0,0]]]
    feat = [[[0,0,0,0],[0,0]],[[0,0,0],[0,0]]]
    if code_srd:
        recurReplace(feat, code2indslist(code_srd))
    features.append(oneHotStructEncode(feat))

    # person(3) template
    # feat = [0,[0,0,0],[0,0,0,0]]
    feat = [[0,0,0,0,0,0],[[0,0,0],0,0,0,0]]
    if code_prs:
        recurReplace(feat, code2indslist(code_prs))
    features.append(oneHotStructEncode(feat))

    # print(features)
    return flattenNested(features)

def getFeatureWithCode(dic, code=None):
    keywords = []
    if code:
        keywords = getNestedKeyWithCode(dic, code)
    all_keywords = getNestedKey(dic)
    return [1 if k in keywords else 0 for k in all_keywords]

def getFeatureSimiWithCode(dic, sent, code=None):
    keywords = []
    if code:
        keywords = getNestedKeyWithCode(dic, code)
    all_keywords = getNestedKey(dic)
    return [maxSentSimi(sent, k) if k in keywords else 0 for k in all_keywords]

def getFeatureWithLayer():
    """
    summarize the layer2code stuff, which head category can be infered from the head code
    """
    pass

def image2feature(layer_names):
    """
    One-hot encode the names of layers
    Get all the keywords recursively
    """

    features = []

    # number of layers
    features.append(len(layer_names))

    # convert to digit codes first
    codes = [name2code(name) for name in layer_names]

    # four layer type, binary
    feat_layer = [0] * 4
    for code in codes:
        feat_layer[code[0] - 1] = 1
    features.append(feat_layer)

    ## todo - summarize this stuff
    # sub-categories, keyword exists - binary
    ## In fact: one-hot in each level, ensured by the codes
    cat_codes = [code[0] for code in codes]
    for c, dic in zip([2, 3], [surrouding_dict, person_dict]):
        if c in cat_codes:
            subcode = codes[cat_codes.index(c)][1:]
        else:
            subcode = None
        features.append(getFeatureWithCode(dic, subcode))

    return flattenNested(features)

def image2SimiFeature(layer_names, sentence):
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
    keywords = []
    if code:
        keywords = getNestedKeyWithCode(dic, code)
    all_keywords = getNestedKey(dic)
    return [sentSimi(sent, k, vocab) if k in keywords else sentSimi(sent, None, vocab) for k in all_keywords]

def getCrossSimi(layer_names, sentence, vocab):
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
