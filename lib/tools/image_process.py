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
def checkLayerName(name, path=None):
    obj = '\[\w+(,\w+)*\]'
    act_obj = '\w+(%s)*' % obj
    reg_single = '\w+(\(%s(,%s)*\))+' % (act_obj, act_obj)
    reg_multi = 'group\(have\[%s(,%s)*\]\)' % (reg_single,
                                               reg_single)
    from ..rules.labels import subjects

    if name.startswith('#background'):
        if not name == '#background':
            raise KeyError(name, path)
    elif name.startswith('#group'):
        if not re.match(r'^#%s$' % reg_multi, name):
            raise KeyError(name, path)
    elif name.startswith('#accessory'):
        if not re.match(r'#accessory(\(%s(,%s)*\))*' % (act_obj, act_obj), name):
            raise KeyError(name, path)
    elif any([name.startswith('#%s' % key) for categ in subjects for key in subjects[categ]]):
        if not re.match(r'^#%s$' % reg_single, name):
            raise KeyError(name, path)
    else:
        raise KeyError(name, path)


def getSubj(layername):
    """
    get the subject of a layername
        E.g. #man(sit_on[chair]) -> man
             #group(have[...]) -> group
             #background -> background
    """
    matched = re.findall(r'^\#(\w+)\(?', layername)
    assert(len(matched) == 1), layername
    return matched[0]


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
        rect_layers = rectifyLayer(path, [cleanName(l.getAttribute('id')) for l in layers])
        for l in rect_layers:
            checkLayerName(l, path)
        return rect_layers
    else:
        if svg.hasAttribute('id') and \
           svg.getAttribute('id').startswith('_x23_'):
            # if single layer case, id should belong to <svg>
            rect_layers = [checkLayerName(cleanName(svg.getAttribute('id')), path)]
            for l in rect_layers:
                checkLayerName(l, path)
            return rect_layers
        else:
            raise ValueError('No valid id name found! %s' % path)


## image synthesis
import os
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

