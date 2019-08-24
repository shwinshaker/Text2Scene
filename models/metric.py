#!./env python

from tools.instance import Node, CombToken
from tools.containers import Picture
from tools.common import enableQuery

@enableQuery
class WeightedMeanIOU:

    def __init__(self, dict_dir='.'):
        self.dict_dir = dict_dir

    def picture_simi(self, p1, p2, thresh=0.1):
        assert(isinstance(p1, Picture))
        assert(isinstance(p2, Picture))

        if not p1.layers_ or not p2.layers_: return 0
        set1 = [l for l in p1.layers_]
        set2 = [l for l in p2.layers_]
        inter_simi = []
        while set1 and set2:
            numerate = [(l1, l2, self.layer_simi(l1.nested_entities_, l2.nested_entities_)) for l1 in set1 for l2 in set2]
            # todo - add layer count attribute to picture instance
            # l1_, l2_, simi_ = sorted(numerate, key=lambda x: (x[-1], x[0].count + x[1].count))[-1]
            l1_, l2_, simi_ = sorted(numerate, key=lambda x: x[-1])[-1]
            if simi_ > thresh:
                set1.remove(l1_)
                set2.remove(l2_)
                inter_simi.append(simi_)
            else:
                break
        simi = sum(inter_simi) / (len(p1) + len(p2) - len(inter_simi))
        assert(simi <= 1.0)
        return simi

    # @classmethod
    def layer_simi(self, layer1_, layer2_):
        """
        layer should be in the form of nested entities
            todo: accept LayerName instance as input
        """
        assert(isinstance(layer1_, dict))
        assert(isinstance(layer2_, dict))
        layer1 = self.ravel_layer(layer1_)
        layer2 = self.ravel_layer(layer2_)

        dic = {'subj': 0.5,
               'act': 0.2,
               'obj': 0.3}
        simi = 0
        for ent in ['subj', 'act', 'obj']:
            if ent != 'act':
                simi += dic[ent] * self.jaccard(layer1[ent], layer2[ent])
            else:
                simi += dic[ent] * self.jaccard_soft(layer1[ent], layer2[ent])
        return simi

    def jaccard(self, set1_, set2_):
        """
        support duplicate elemenets
        """
        assert(isinstance(set1_, list))
        assert(isinstance(set2_, list))
        if not set1_ or not set2_: return 0

        set1, set2 = set1_.copy(), set2_.copy()
        inter = []
        while True:
            intersec = [n for n in set1 if n in set2]
            if intersec:
                for n in set(intersec):
                    set1.remove(n)
                    set2.remove(n)
                    inter.append(n)
            else:
                break
        simi_ = len(inter) / (len(set1_) + len(set2_) - len(inter))
        assert(simi_ <= 1.0)
        return simi_

    def jaccard_soft(self, set1_, set2_, thresh=0.3):
        assert(isinstance(set1_, list))
        assert(isinstance(set2_, list))

        if not set1_ or not set2_: return 0
        assert(isinstance(set1_[0], Node))

        set1, set2 = set1_.copy(), set2_.copy()
        inter_simi = []
        while set1 and set2:
            numerate = [(n1, n2, self.query_simi(n1.t, n2.t)) for n1 in set1 for n2 in set2]
            n1_, n2_, simi_ = sorted(numerate, key=lambda x: (x[-1], x[0].count + x[1].count))[-1]
            if simi_ > thresh:
                set1.remove(n1_)
                set2.remove(n2_)
                inter_simi.append(simi_)
            else:
                # the most simi pairs won't pass the threshold
                break
        simi = sum(inter_simi) / (len(set1_) + len(set2_) - len(inter_simi))
        assert(simi <= 1.0)
        return simi

    def fetch_keyword(self, comb, attr):
        if isinstance(comb, Node): return comb
        # if comb.keyword: return comb.keyword
        # return Node(comb.token.lemma_, attr)
        if comb.token: return Node(comb.token.lemma_, attr)
        return comb.keyword

    def ravel_layer(self, layer):
        # should be list? what if duplicate keywords
        # entities_ = {'subj': set(), 'act': set(), 'obj': set()}
        entities_ = {'subj': [], 'act': [], 'obj': []}
        for subj in layer:
            entities_['subj'].append(self.fetch_keyword(subj, 'subj'))
            for act in layer[subj]:
                entities_['act'].append(self.fetch_keyword(act, 'act'))
                for obj in layer[subj][act]:
                     entities_['obj'].append(self.fetch_keyword(obj, 'obj'))
        return entities_

