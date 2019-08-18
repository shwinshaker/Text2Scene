#!./env python

import re
from xml.dom.minidom import parse

def dict_ai2puncs_():
    dic = {}
    dic['_x23_'] = '#'
    dic['_x28_'] = '('
    dic['_x29_'] = ')'
    dic['_x5B_'] = '['
    dic['_x5D_'] = ']'
    dic['_x2C_'] = ','
    dic['_x5F_'] = '-'
    return dic

def cleanName(s):
    s = multiple_replace(dict_ai2puncs_(), s)
    s = re.sub('_x?\d+_', '', s) # remove other symbols
    s = re.sub('_', '', s) # remove _  (space)

    return re.sub('-', '_', s) # replace - back to _

def multiple_replace(dic, text):
    """
    mutiple regex substitutions
        Bug: keys that are prefixes of other keys will break
    """
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape,
                                             dic.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo:
                     dic[mo.string[mo.start():mo.end()]],
                     text)

def rectifyLayer(path, li):
    """
    something to do to rectify the layer order to reduce composition freedom
    """
    return li


## 2.0
def getLayerNames(path):
    """
    Get the name of each layer in the image
        first check the id attribute of <svg>
        then check the id attribute of <g>s
    """
    assert(isinstance(path, str)), path
    assert(path.endswith('.svg')), path

    doc = parse(path)
    svg_list = doc.getElementsByTagName('svg')
    assert(len(svg_list) == 1)
    svg = svg_list[0]
    # use * instead of g, some layer may not be a group
    layers = [g for g in doc.getElementsByTagName('*') \
              if g.nodeType == 1 and \
                 g.hasAttribute('id') and \
                 g.getAttribute('id').startswith('_x23_')]

    if layers:
        return rectifyLayer(path, [cleanName(l.getAttribute('id')) for l in layers])
    else:
        if svg.hasAttribute('id') and \
           svg.getAttribute('id').startswith('_x23_'):
            # if single layer case, id should belong to <svg>
            return [cleanName(svg.getAttribute('id'))]
        else:
            raise ValueError('No valid id name found!')


