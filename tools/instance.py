#!./env python

from collections import defaultdict

class Node:
    def __init__(self, t, attr, count=1):
        self.t = t
        self.attr = attr
        self.count = count
        self.neighbors = defaultdict(lambda: defaultdict(Node))

    def __str__(self):
        return '%s(%s)' % (self.t, self.attr)

    def __eq__(self, other):
        """
        must implement this to support comparation between nodes
        """
        if not isinstance(other, Node):
            raise TypeError((other, type(other)))
        return self.t == other.t and self.attr == other.attr

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.t < other.t or (self.t == other.t and self.attr < other.attr)

    def __hash__(self):
        """
        need to explicitly implement hash function to make it hashable if __eq__ is implemented
        seems to recommend xor.
           see. https://stackoverflow.com/questions/4005318/how-to-implement-a-good-hash-function-in-python
                https://stackoverflow.com/questions/2909106/whats-a-correct-and-good-way-to-implement-hash
        """
        return hash((self.t, self.attr))

    def __repr__(self):
        return self.__str__()


class Picture:
    """
    possible usage:
        picture = Picture('images/Firmware.svg')
        [n.t for n in picture.ravel_]
        picture.plot()
    """
    def __init__(self, img_name=None, layernames=None):
        """
        either built from file, or from self-punched layer names
        """
        if img_name:
            self.img_name = img_name
            self.layernames_ = getLayerNames(img_name)
        else:
            warnings.warn('Caveats! img name bypassed!')
            assert(layernames)
            self.layernames_ = layernames

        self.layer_merge_ = LayerName()
        self.layers_ = []
        for layername in self.layernames_:
            layer = LayerName(layername)
            self.layers_.append(layer)
            self.layer_merge_.absorb(layer)
        # make the layers immutable
        self.layers_ = tuple(self.layers_)
        self.plot = self.layer_merge_.plot

        # vocab is a set, no duplicates
        self.vocab_ = ravel(self.layer_merge_.entities_)

        self.triple_set_ = set([layer.triples_ for layer in self.layers_])

    def __repr__(self):
        """
        used to print a string when directly call the object?
        also used to compare if two pictures are same. same as __eq__?
        """
        return '; '.join(self.layernames_)

    def __eq__(self, other):
        # should consider overlapping order here?
        # but it should make no difference if ravel the keywords as features
        # lets omit it for now
        # ! the order of layers doesn't matter
        return self.triple_set_ == other.triple_set_

    def __hash__(self):
        return hash(tuple(self.triple_set_))


class Description:
    """
    save tokens and original sentence
    """
    def __init__(self, txt_name=None, text=None):
        if txt_name:
            self.txt_name = txt_name
            with open(txt_name) as f:
                self.text_ = f.read()
        else:
            warnings.warn('Caveats! txt name bypassed!')
            assert(text)
            self.text_ = text

        tokenizer = SpacyLemmaTokenizer()
        self.tokens_ = tokenizer(self.text_)

        # vocab is a set, no duplicates
        self.vocab_ = set(self.tokens_)

    def __repr__(self):
        return self.text_

    def __eq__(self, other):
        assert(isinstance(other, Description))
        return self.text_ == other.text_

    def __hash__(self):
        return hash(self.text_)

