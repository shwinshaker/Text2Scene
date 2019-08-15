#!./env python

from tools.text_process import LemmaTokenizer
from tools.common import ravel
from tools.instance import Node
from tools.image_process import LayerName, getLayerNames

import glob

class LayerBase():
    def __init__(self):

        layername = LayerName()
        for svg in glob.glob('images/*.svg'):
            for layer in getLayerNames(svg):
                layername.absorb(LayerName(layer))
        self.entities_ = layername.entities_
        # self.keywords_ = sorted(list(ravel(layername.entities_)),
        #                           key=lambda n: (n.t, n.attr))
        self.keywords_ = sorted(ravel(layername.entities_))

    # def index(self, keyword, attr):
    #     return self.nodes_.index(Node(keyword, attr))

    def index(self, keyword):
        assert(isinstance(keyword, Node))
        return self.keywords_.index(keyword)

    def __len__(self):
        return len(self.keywords_)

class TextBase():
    def __init__(self):
        vocab = set()
        tokenizer = LemmaTokenizer()
        for txt in glob.glob('text/*.txt'):
            with open(txt) as f:
                text = f.read()
            tokens = tokenizer(text)
            vocab |= set(tokens)
        self.vocab_ = sorted(vocab)

    def index(self, token):
        assert(isinstance(token, Node))
        return self.vocab_.index(token)

    def __len__(self):
        return len(self.vocab_)
