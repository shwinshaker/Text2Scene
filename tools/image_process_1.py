#!./env python

from xml.dom.minidom import parse
import os
import numpy as np
import glob
import re
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
            # assert(len([g for g in svg.childNodes \
            #               if g.nodeType == 1 and \
            #                  g.tagName == 'g']) <= 1), file
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


class Edges:
    def __init__(self):
        self.edges = set()
    
    def add(self, node1, node2):
        self.edges.add((node1, node2))
        
    def __iter__(self):
        for e in self.edges:
            yield e
        
    def _print(self):
        for n1, n2 in sorted(list(self.edges), key=lambda e: (e[0].attr, 
                                                              e[1].attr,
                                                              e[0].t,
                                                              e[1].t)):
            print('%s - %s' % (n1.__str__(), n2.__str__()))
        
class Graph:
    """
    see. https://stackoverflow.com/questions/19472530/representing-graphs-data-structure-in-python
        Deprecated!
    """
    def __init__(self, s=None):
        # pattern
        self.obj_ptn = '\[\w+(,\w+)*\]'
        self.act_obj_ptn = '\w+(%s)*' % self.obj_ptn
        self.single_ptn = '\w+(\(%s(,%s)*\))*' % (self.act_obj_ptn,
                                                  self.act_obj_ptn)
        self.group_ptn = '%s\(%s\[%s(,%s)*\]\)' % ('group',
                                                   'have',
                                                    self.single_ptn,
                                                    self.single_ptn)
        
        if s:
            self.s = s
            
            # get all entity names
            self.subjs_ = self.subjs()
            self.acts_ = self.acts()
            self.objs_ = self.objs()
            
            # instantiate a list
            self.nodes_ = defaultdict(lambda: defaultdict(Node))
            for subj in self.subjs_:
                self.nodes_['subj'][subj] = Node(subj, 'subj')
            for act in self.acts_:
                self.nodes_['act'][act] = Node(act, 'act')
            for obj in self.objs_:
                self.nodes_['obj'][obj] = Node(obj, 'obj')
            
            # add edges
            # assume that repetitive objects refer to the same one
            #        when instantiate from a layer name
            #        thus no need to check duplicate
            for subj in self.subjs_:
                for act in self.acts_:
                    if self.is_connect_subj_act(subj, act):
                        self.nodes_['subj'][subj].neighbors['act'][act] = self.nodes_['act'][act]
                        self.nodes_['act'][act].neighbors['subj'][subj] = self.nodes_['subj'][subj]
            for act in self.acts_:
                for obj in self.objs_:
                    if self.is_connect_act_obj(act, obj):
                        self.nodes_['act'][act].neighbors['obj'][obj] = self.nodes_['obj'][obj]
                        self.nodes_['obj'][obj].neighbors['act'][act] = self.nodes_['act'][act]
            for obj in self.objs_:
                for subj in self.subjs_:
                    if self.is_connect_subj_obj(subj, obj):
                        self.nodes_['obj'][obj].neighbors['subj'][subj] = self.nodes_['subj'][subj]
                        self.nodes_['subj'][subj].neighbors['obj'][obj] = self.nodes_['obj'][obj]

    def __check(self):
        if not re.match(r'^#%s$' % self.single_ptn, self.s):
            if not re.match(r'^#%s$' % self.group_ptn, self.s):
                raise KeyError(self.s)
                
    def subjs(self):
        if self.s.startswith('#background'):
            return {'background'}
        if self.s.startswith('#accessory'):
            return {'accessory'}
        if self.s.startswith('#group'):
            subjs = re.findall('[\[|,](\w+)\(', self.s)
        else:
            subjs = re.findall('^#(\w+)\(', self.s)
            assert len(subjs) == 1, (self.s, subjs)
        assert(len(subjs) == len(set(subjs)))
        return set(subjs)

    def acts(self, subjs):
        assert(isinstance(subjs, list))
        # give subj, find associated actions
        # if group, remove group mark
        if self.s.startswith('#group'):
            s = re.sub('#group\(have\[', '', self.s)
            s.strip('\]\)')
        else:
            s = self.s

        # temporarily remove all objects
        obj = '\[\w+(,\w+)*\]'
        s = re.sub(obj, '', s)

        # extend or append
        acts = defaultdict(list)
        for subj in subjs:
            for act in re.findall(r'{subj}\((.*?)\)'.format(subj=subj), s):
                if ',' in act:
                    acts[subj].extend(act.split(','))
                else:
                    acts[subj].append(act)

        return acts

    def objs(self):
        # if group, remove group mark
        if self.s.startswith('#group'):
            s = re.sub('#group\(have\[', '', self.s)
            s.strip('\]\)')
        else:
            s = self.s

        # extend or append
        objs = []
        for obj in re.findall(r'\[(.*?)\]', s):
            if ',' in obj:
                objs.extend(obj.split(','))
            else:
                objs.append(obj)

        return set(objs)

    def entities_(self):
        return {'subjects': self.subjs_(),
                'actions': self.acts_(),
                'objects': self.objs_()}
    
    def to_node(self, t):
        if t in self.subjs_:
            return Node(t, 'subj')
        elif t in self.acts_:
            return Node(t, 'act')
        elif t in self.objs_:
            return Node(t, 'obj')
        else:
            raise ValueError('%s not in graph!' % t)
            
    def is_connect(self, t1, t2):
        """
        Wrapper for connection between two entities
            a problem will happen if a word can either be verb and noun
                better indicate attribute when query
        """
        if (self.to_node(t1), self.to_node(t2)) in self.edges_:
            return True
        else:
            return (self.to_node(t2), self.to_node(t1)) in self.edges_

    def is_connect_subj_obj(self, subj, obj):
        obj_pat = '\[\w+(,\w+)*\]'
        act_obj_pat = '\w+(%s)*' % obj_pat
        if re.match(r'.*?%s\((%s,)*\w+\[(\w+,)*%s(,\w+)*\](,%s)*\).*?' % (subj, act_obj_pat, obj, act_obj_pat), self.s):
            return True
        return False

    def is_connect_act_obj(self, act, obj):
        if re.match(r'.*?%s\[(\w+,)*%s(,\w+)*\].*?' % (act, obj), self.s):
            return True
        return False

    def is_connect_subj_act(self, subj, act):
        if subj == 'group':
            if re.match(r'#%s\(%s.*?\)$' % (subj, act), self.s):
                return True
            return False

        obj = '\[\w+(,\w+)*\]'
        act_obj = '\w+(%s)*' % obj
        if re.match(r'.*?%s\((%s,)*%s(%s)*(,%s)*\).*?' % (subj, act_obj, act, obj, act_obj), self.s):
            return True
        return False
    
    def merge(self, other):
        """
        should use same reference in edges and nodes
            so what about dict(set)?
        """
        assert isinstance(other, Graph), 'the other one is not a graph'
        graph = Graph()
        graph.subjs_ = self.subjs_ | other.subjs_
        graph.acts_ = self.acts_ | other.acts_
        graph.objs_ = self.objs_ | other.objs_
        graph.edges_ = self.edges_
        graph.nodes_ = self.nodes_
        for n1, n2 in other.edges_:
            if (n1, n2) in graph.edges_:
                for e in graph.edges_:
                    if e == (n1, n2):
                        e[0].count += 1
                        e[1].count += 1
                for n in graph.nodes_:
                    if n == n1 or n == n2:
                        n.count += 1
            elif n1 in graph.nodes_:
                for n in graph.nodes_:
                    if n == n1:
                        n.count += 1
            elif n2 in graph.nodes_:
                for n in graph.nodes_:
                    if n == n2:
                        n.count += 1

    def print_(self):
        for n1, n2 in sorted(list(self.edges_), key=lambda e: (e[0].attr, 
                                                               e[1].attr,
                                                               e[0].t,
                                                               e[1].t)):
            print('%s - %s' % (n1.__str__(), n2.__str__()))
            
    def plot(self):
        import matplotlib.pyplot as plt
        figsize = (5, max(len(self.subjs_), len(self.acts_), len(self.objs_))/6*2)
        plt.figure(figsize=figsize)
        plt.plot([1]*len(self.subjs_), range(len(self.subjs_)),'r.')
        plt.plot([2]*len(self.acts_), range(len(self.acts_)),'g.')
        plt.plot([3]*len(self.objs_), range(len(self.objs_)), '.', color='orange')
        
        def get_xy(node):
            if node.attr == 'subj':
                return (1, sorted(list(self.subjs_)).index(node.t))
            elif node.attr == 'act':
                return (2, sorted(list(self.acts_)).index(node.t))
            elif node.attr == 'obj':
                return (3, sorted(list(self.objs_)).index(node.t))
            else:
                raise KeyError(attr)
            
        for edge in self.edges_:
            xs, ys = list(zip(get_xy(edge[0]), get_xy(edge[1])))
            if 'act' in [edge[0].attr, edge[1].attr]:
                if edge[0].t != 'have' and edge[1].t != 'have':
                    plt.plot(xs, ys, 'k-', alpha=0.1)
                else:
                    node = edge[1] if edge[0].t == 'have' else edge[0]
                    for edge_ in self.edges_:
                        if node in edge_ and edge_[0].t != 'have' and edge_[1].t != 'have':
                            xs, ys = list(zip(get_xy(edge_[0]), get_xy(edge_[1])))
                            plt.plot(xs, ys, 'k--', alpha=0.1)
        
                
        for i, subj in enumerate(sorted(list(self.subjs_))):
            plt.text(1, i, subj, color='r')
        for i, act in enumerate(sorted(list(self.acts_))):
            plt.text(2, i, act, color='g')
        for i, obj in enumerate(sorted(list(self.objs_))):
            plt.text(3, i, obj, color='orange')
        plt.axis('off')
        plt.show()
