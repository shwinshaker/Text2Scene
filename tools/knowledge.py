#!./env python

from tools.common import ravel
from tools.instance import Node
from tools.containers import Picture, Description, LayerName
from tools.common import ddict2dict

import glob

class LayerBase():
    """
    layer Base knowledge, show only built on train set!
    """
    def __init__(self, filenames=[],
                 img_dir='images',
                 ext='.svg'):

        """
        need other dictionary to save the layer frequency
        """
        if not filenames:
            filenames = glob.glob('%s/*%s' % (img_dir, ext))
        else:
            filenames = ['%s/%s%s' % (img_dir, name, ext) for name in filenames]

        # self.layer_merge_ = LayerName()
        layer_merge_ = LayerName()
        self.pictures_ = []
        for svg in filenames:
            picture = Picture(svg)
            # for layer in getLayerNames(svg):
            #     layername = LayerName(layer)
            #     self.layers_.append(layername)
            # self.layer_merge_.absorb(picture.layer_merge_)
            layer_merge_.absorb(picture.layer_merge_)
            self.pictures_.append(picture)
        # self.entities_ = self.layer_merge_.entities_
        # prevent empty query change the key
        self.entities_ = layer_merge_.entities_
        self.collocations_ = layer_merge_.nested_entities_

        # picture vocab contains no dupicates
        self.pic_vocab_ = set(self.pictures_)

        # layer vocab contains no dupicates
        self.layer_vocab_ = set([layer for picture in self.pictures_ for layer in picture.layers_])

        # keyword vocab contains no dupicates
        # here we explicitly need the order the make sure results reproducable
        ## such as index and line up features
        self.vocab_ = sorted(ravel(self.entities_))

        self.plot = layer_merge_.plot

    def index(self, keyword):
        assert(isinstance(keyword, Node))
        return self.vocab_.index(keyword)

    def __len__(self):
        return len(self.vocab_)


class TextBase():
    def __init__(self, filenames=[],
                 txt_dir='text',
                 ext='.txt'):

        if not filenames:
            filenames = glob.glob('%s/*%s' % (txt_dir, ext))
        else:
            filenames = ['%s/%s%s' % (txt_dir, name, ext) for name in filenames]

        self.vocab_ = set()
        self.doc_vocab_ = set()
        for txt in filenames:
            doc = Description(txt)
            self.vocab_ |= doc.vocab_
            self.doc_vocab_.add(doc)
        self.vocab_ = sorted(self.vocab_)

    def index(self, token):
        assert(isinstance(token, Node))
        return self.vocab_.index(token)

    def __len__(self):
        return len(self.vocab_)

    def __iter__(self):
        return iter(self.vocab_)
