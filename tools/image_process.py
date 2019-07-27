#!./env python

from xml.dom.minidom import parse
import os
import numpy as np
import glob
import re
from rules.category import person_dict, surrouding_dict
from tools.common import flattenNested, extractLeaf, getDepth
from tools.common import getNestedKey, getNestedKeyWithCode
from tools.joint_process import wrapRelaxedSimi
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
        return rectifyLayer(file, [cleanName(l.getAttribute('id')) for l in f_layers])
    else:
        if svg.hasAttribute('id'):
            # if single layer case, id belongs to <svg>
            # todo - check there be at most 1 <g> on each level
            assert(len([g for g in svg.childNodes \
                          if g.nodeType == 1 and \
                             g.tagName == 'g']) <= 1)
            return [cleanName(svg.getAttribute('id'))]
        else:
            raise ValueError('No valid id name found!')

def rectifyLayer(file, layers):
    """
    move A4 to the top, let's forget the position of decoration tentatively
    move A3 on top of A2, let's forget the relative position between person and surroundings tentatively
    """
    firstTwo = [l[:2] for l in layers]
    if 'A2' in firstTwo and 'A3' in firstTwo:
        if firstTwo.index('A2') > firstTwo.index('A3'):
            warnings.warn('In image %s A2 is on the top of A3! Exchange them!' % file, RuntimeWarning)
            a3 = layers[firstTwo.index('A3')]
            layers.remove(a3)
            layers.insert(firstTwo.index('A2')+1, a3)

    if 'A4' in layers:
        if layers.index('A4') != len(layers) - 1:
            warnings.warn('In image %s A4 is not at the top! Move it to the top!' % file, RuntimeWarning)
            layers.remove('A4')
            layers.append('A4')

    return layers

def cleanName(name):
    """
    remove irregular marks in adobe illustrator
    """
    return re.sub('_x?\d+_','',name)

def name2code(name):
    """
    input: 'A-1-2-3-4' or 'A1234'
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

    ## if decoration in, it must be the most top or bottom layer
    # if 4 in cat_codes:
    #     assert(cat_codes.index(4) == 0 or cat_codes.index(4) == len(cat_codes) - 1), 'decoration should be the most top or bottom!'

    # if decoration in, it must be the most top layer
    # Let's assert this for now
    if 4 in cat_codes:
        assert(cat_codes.index(4) == len(cat_codes) - 1), 'decoration should be the most top!'

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
                               '_Decoration_'])
                               # '_P_in_front_of_S_',
                               # '_S_in_front_of_P_'])

        # categorical features
        self.srd_categ = getNestedKey(surrouding_dict)
        self.prs_categ = getNestedKey(person_dict)
        self.category_ = self.srd_categ + self.prs_categ
        self.features_.extend(['_S_%s_' % k for k in self.srd_categ])
        self.features_.extend(['_P_%s_' % k for k in self.prs_categ])

        # pair features
        self.features_.extend(['_S_%s-P_%s_' % (ks, kp) for ks in self.srd_categ for kp in self.prs_categ])

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

        """
        Let's resolve the occlusion tentatively.
        The case that surrounding in front of person is too rare and make the reality discriminator too easy.
        The only case that surrounding should be in front of person:
            14.svg
        """
        # # occlusion, person in front of surrounding, or otherwise
        # cat_codes = [code[0] for code in codes]
        # if 2 in cat_codes and 3 in cat_codes:
        #     if cat_codes.index(2) < cat_codes.index(3):
        #         # person in the front
        #         features.append([1,0])
        #     else:
        #         # surrounding in the front
        #         features.append([0,1])
        # else:
        #     features.append([0,0])

        # sub-categories, keyword exists - binary
        ## In fact: one-hot in each level, ensured by the codes
        features.append(self.keyword2feature(self.layer2keyword(layer_names)))

        # cross similarities between subcategories
        features.append(self.crossSimi(layer_names))

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

    def crossSimi(self, layer_names):
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes] # get head category

        srd_keys = []
        if 2 in cat_codes:
            subcode = codes[cat_codes.index(2)][1:]
            srd_keys = getNestedKeyWithCode(surrouding_dict, subcode)

        prs_keys = []
        if 3 in cat_codes:
            subcode = codes[cat_codes.index(3)][1:]
            prs_keys = getNestedKeyWithCode(person_dict, subcode)

        return [wrapRelaxedSimi(ks, kp) if ks in srd_keys and kp in prs_keys else 0 for ks in self.srd_categ for kp in self.prs_categ]


### Image synthesis
def str2num_size(size):
    """
    Convert a size string into a digit
    Eg. 12pt -> 12
    """
    assert type(size) is str
    return int(float(size.strip('pt')))

def get_size(file):
    """
    Get the width and height of an image

    .svg:
        use xml's parse
        By check the 'viewBox' attribute in the 'svg' tag

    .png:
        use PIL
    """

    basename, ext = os.path.splitext(file)
    if ext == '.svg':
        from xml.dom.minidom import parse
        doc = parse(file)
        # search svg element
        image_list = doc.getElementsByTagName('svg')
        assert(image_list), 'no svg element found!'
        assert(len(image_list) == 1), file
        img = image_list[0]
        assert(img.hasAttribute('viewBox'))
        width, height = img.getAttribute('viewBox').split()[2:]
        width, height = (str2num_size(width), str2num_size(height))
        # try search image element, then g element
#     try:
#         assert image_list
#     except AssertionError:
#         image_list = doc.getElementsByTagName('svg')
#         assert image_list
#         assert image_list[0].hasAttribute('width')
#     assert(len(image_list) == 1), svg_file
#     ## if multiple images, size is the maximum size in either direction
    elif ext == '.png':
        from PIL import Image
        width, height = Image.open(file).size

    return (width, height)

def stack_svgs(file_list, opt_file=None, canvas_size=None):
    """
    Stack materials into a .svg image
        Support .png material only
    """

    import cairosvg
    from svgutils.compose import Figure, Image #,SVG

    if not opt_file:
        opt_file = 'stack.svg'

    if canvas_size:
        canvas_w, canvas_h = canvas_size
    else:
        canvas_w, canvas_h = 0, 0
        for file in file_list:
            width, height = get_size(file)
            if width > canvas_w: canvas_w = width
            if height > canvas_h: canvas_h = height
    print('Canvas size:', (canvas_w, canvas_h))

    # if svg, convert to png first
    file_list_png = []
    for file in file_list:
        basename, ext = os.path.splitext(file)
        if ext == '.svg':
            png_file = basename + '.png'
            cairosvg.svg2png(url=file,
                             write_to=png_file)
            file_list_png.append(png_file)
        elif ext == '.png':
            file_list_png.append(file)
        else:
            raise ValueError('File type not availale!')

    image_list = []
    #
    for file in file_list_png:
        print('File:', file)
        width, height = get_size(file)
        img = Image(width, height, file)
        img.move(int((canvas_w-width)/2),
                 int((canvas_h-height)/2))
        image_list.append(img)

    Figure(canvas_w, canvas_h, *image_list).save(opt_file)
