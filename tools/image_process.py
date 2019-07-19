#!./env python

from xml.dom.minidom import parse
import os
import numpy as np
import glob
import re
from itertools import count


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
    layers = [g for g in svg.childNodes \
              if g.nodeType == 1 and \
                 g.tagName == 'g' and \
                 g.hasAttribute('id')]
    if layers:
        return [l.getAttribute('id') for l in layers]
    else:
        if svg.hasAttribute('id'):
            # if single layer case, id belongs to <svg>
            assert(len([g for g in svg.childNodes \
                          if g.nodeType == 1 and \
                             g.tagName == 'g']) == 1)
            return [svg.getAttribute('id')]
        else:
            raise ValueError('No valid id name found!')

def name2code(name):
    """
    input: A-1-2-3-4
    output: [1,2,3,4]
    """
    return [int(d) for d in name.split('-')[1:]]

def checkLayerNames(names):
    """
    Check if the names of layers we got make sense
    """
    ### styling check
    # names of layers must start with 'A-'
    for name in names:
        assert(name.startswith('A-')), "%s does not start with A-" % name

    # names of layers should match \d-\d
    for name in names:
        assert(re.match(r'A(-\d)+', name)), "%s does not match the pattern!" % name

    ### sanity check
    cat_codes = [name2code(s)[0] for s in names]

    # if background in, it must be the most bottom layer
    if 1 in cat_codes:
        assert(cat_codes.index(1) == 0), 'background should be the most bottom!'

    # if decoration in, it must be the toppest layer
    if 4 in cat_codes:
        assert(cat_codes.index(4) == len(cat_codes) - 1), 'decoration should be the most top!'

    if len(cat_codes) == 1:
        # if only one layer, must be surrounding layer
        assert(cat_codes[0] == 2), 'it must be the surrounding layer if there is only one layer'
    else:
        # if multiple layers, check the cat order
        # background 1 - surroundings 2 - person 3 - decoration 4
        for code1, code2 in zip(cat_codes[:-1], cat_codes[1:]):
            assert(code2 > code1), \
               'layer %s should not be below layer %s!' % (code2, code1)


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


def image2feature(layer_names):
    """
    One-hot encode the names of layers
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
    feat = [[0,[0,0,0]],[0,[0,0,0],[0,0]]]
    if code_srd:
        recurReplace(feat, code2indslist(code_srd))
    features.append(oneHotStructEncode(feat))

    # person(3) template
    feat = [0,[0,0,0],[0,0,0,0]]
    if code_prs:
        recurReplace(feat, code2indslist(code_prs))
    features.append(oneHotStructEncode(feat))

    # print(features)
    return flattenNested(features)
