#!./env python

from xml.dom.minidom import parse
import os
import numpy as np
import glob
import re
from rules.category import person_dict, surrouding_dict
from tools.common import flattenNested, extractLeaf, getDepth
from tools.common import getNestedKey, getNestedKeyWithCode
import warnings

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
        ## only find those layers at the same level
        f_layers = [layers[0]]
        for layer in layers[1:]:
            # assert(layer in layers[0].parentNode.childNodes), ('Ids not at the same level!: %s' % file, layers)
            if layer in layers[0].parentNode.childNodes:
                f_layers.append(layer)
            else:
                warnings.warn('In file %s layer %s not at the same level with the first layer! Skip it!' % (file, layer.getAttribute('id')))
        return [l.getAttribute('id') for l in f_layers]
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

    # # if only one layer, must be surrounding layer
    # if len(cat_codes) == 1:
    #     assert(cat_codes[0] == 2), 'it must be the surrounding layer if there is only one layer'
    # else: ## not necessarily
    #     # if multiple layers, check the cat order
    #     # background 1 - surroundings 2 - person 3 - decoration 4
    #     for code1, code2 in zip(cat_codes[:-1], cat_codes[1:]):
    #         assert(code2 > code1), \
    #            'layer %s should not be below layer %s!' % (code2, code1)


### From layer name to image features
class CategEncoder():
    def __init__(self):

        # get feature names
        self.features_ = []
        self.features_.append('_NLayers_')
        self.features_.extend(['_Background_',
                               '_Surroundings_',
                               '_Person_',
                               '_Decoration_',
                               '_P_in_front_of_S_',
                               '_S_in_front_of_P_'])

        # categorical features
        self.srd_categ = getNestedKey(surrouding_dict)
        self.prs_categ = getNestedKey(person_dict)
        self.category_ = self.srd_categ + self.prs_categ
        self.features_.extend(['_S_%s_' % k for k in self.srd_categ])
        self.features_.extend(['_P_%s_' % k for k in self.prs_categ])

    def encode(self, layer_names):

        features = []
        # number of layers
        features.append(len(layer_names))

        # convert to digit codes first
        codes = [name2code(name) for name in layer_names]

        # four types of layers, binary
        feat_layer = [0] * 4
        for code in codes:
            feat_layer[code[0] - 1] = 1
        features.append(feat_layer)

        # occlusion, person in front of surrounding, or otherwise
        cat_codes = [code[0] for code in codes]
        if 2 in cat_codes and 3 in cat_codes:
            if cat_codes.index(2) < cat_codes.index(3):
                # person in the front
                features.append([1,0])
            else:
                # surrounding in the front
                features.append([0,1])
        else:
            features.append([0,0])

        # sub-categories, keyword exists - binary
        ## In fact: one-hot in each level, ensured by the codes
        features.append(self.keyword2feature(self.layer2keyword(layer_names)))

        return flattenNested(features)

    def keyword2feature(self, keywords):
        """
        Convert category keywords to one-hot features
        """
        return [1 if k in keywords else 0 for k in self.category_]

    def layer2keyword(self, layer_names):
        """
        convert layer names to category keywords, but lose the occlusion info
            Person and surrounding only
        """
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes] # get head category

        keywords = []
        for c, dic in zip([2, 3], [surrouding_dict, person_dict]):
            if c in cat_codes:
                subcode = codes[cat_codes.index(c)][1:]
                keywords.extend(getNestedKeyWithCode(dic, subcode))
        return keywords



