#!./env python

from tools.instance import Node, VerbNode, CombToken
from tools.common import QuerySimi, getElementFromSet
import networkx as nx
import spacy

from tools.common import enableQuery_, enableQuery
from rules.consts import UNK, MISSED

# @enableQuery_
# @enableQuery
class KeywordGrounder:

    def __init__(self, vocabbase):
        # self.query = QuerySimi()
        self.base = vocabbase

    def __call__(self, G):
        assert(isinstance(G, nx.classes.graph.Graph))
        return nx.freeze(self.ground_action(self.ground_entity(G)))

    def query_(self, token, k):
        try:
            simi = self.query(token.lemma_, k.t)
        except AssertionError:
            simi = self.query(token.text, k.t)
        return simi

    def get_simi_keyword(self, token, keywords, thresh=0.2): #0.3
    # def get_simi_keyword(self, token, keywords, thresh=0.0):
        assert(isinstance(keywords, set))
        assert(isinstance(list(keywords)[0], Node))
        assert(isinstance(token, spacy.tokens.token.Token))
        # tups = [(k, self.query(token.lemma_, k.t)) for k in keywords]
        # tups = [(k, self.query_simi(token.lemma_, k.t)) for k in keywords]
        tups = [(k, self.base.query_simi(token.lemma_, k.t)) for k in keywords]
        # tups = [(k, self.query_(token, k)) for k in keywords]
        simi_key, simi_ = sorted(tups, key=lambda x: (x[1], x[0].count))[-1]
        if simi_ >= thresh:
            if simi_key.attr == 'act':
                # use token lemma
                return CombToken(token,
                                 Node(token.lemma_, simi_key.attr))
            else:
                # use keyword name in base
                # use token.i to resolve conflict
                return CombToken(token,
                                 Node(simi_key.t, simi_key.attr, token.i))
        if list(keywords)[0].attr == 'act':
            # return CombToken(token, VerbNode(UNK, attr='act'))
            # return CombToken(token, Node(UNK, attr='act'))
            return CombToken(token, Node(token.lemma_, attr='act'))
        else:
            # todo - may need to specify either attrbute here to comform to the convention
            # gloVe didn't involve this part..
            # probably because conceptnet relatedness is lower in general
            # return CombToken(token, VerbNode(UNK, attr='[subj|obj]'))
            # return CombToken(token, Node(UNK, attr='[subj|obj]'))
            # return CombToken(token, Node(token.lemma_, attr='[subj|obj]'))
            # return CombToken(token, Node(token.lemma_, attr='obj'))
            return CombToken(token, Node(MISSED, attr='obj'))

    def ground_entity(self, g):
        """
        require noun base
        """
        mapping = {}
        for node in g.nodes:
            mapping[node] = self.get_simi_keyword(node.root, self.base.nouns_)
        return nx.relabel_nodes(g, mapping)

    def ground_action(self, g_):
        """
        require verb base
        """
        g = g_.copy()
        for u, v, e in g.edges(data='verb'):
            combtoken = self.get_simi_keyword(e.root, set(self.base.verbs_.keys()))
            g[u][v]['verb'] = combtoken
            g[u][v]['intension'] = self.base.get_intension(combtoken.keyword, verbose=False)
        for u, a_l in g.nodes(data='verbs'):
            if a_l:
                combtokens = set()
                for a in a_l:
            # if a:
                    combtokens.add(self.get_simi_keyword(a.root, set(self.base.verbs_.keys())))
                # combtoken = self.get_simi_keyword(a.root,
                #                              set(self.base.verbs_.keys()))
            # g.node[u]['verb'] = combtoken
                g.node[u]['verbs'] = combtokens
                # g.node[u]['intension'] = get_intension(combtoken.keyword, verbose=False)
                # intension should be bound with verb each.
                # Will not use it.
        return g


import networkx as nx
import itertools
from tools.containers import GraphSpan

class GraphManipulator:
    """
    shuffle weakly connected objects
    """

    def __init__(self):
        pass

    # def get_generator(self):
    def __call__(self, g):
        assert(isinstance(g, GraphSpan))
        # fixed_set = self.get_triples(strong_only=True)

        # remove all the weakly connected nodes first
        # later add back newly formed edges and nodes
        g_base = g.copy()
        for n in g.get_objs(weak_only=True):
            g_base.G.remove_node(n)

        for triplets in self.get_weak_triplets(g):
            # comb_set = [self.rectify(*tup) for tup in weak_comb]
            g_ = g_base.copy()
            g_.G.add_edges_from([g_.to_edge(g_.rectify(*t)) for t in triplets])
            yield g_

    def get_weak_triplets(self, g):
        subjs = g.get_subjs()
        objs = g.get_objs(weak_only=True)

        matrix = []
        for o in objs:
            li = []
            # first add the orignial weakly connected triplets as a possibility
            ## object connected to multiple subjects should be considered simutaneously
            all_weaks = []
            for s in g.G.neighbors(o):
                if not g.is_strong(s, o) and g.is_subj(s):
                    all_weaks.append((s, g.G[s][o]['verb'], o))
            if all_weaks:
                li.append(tuple(all_weaks))

            # then for each other non-neighour subjects, try bind this object to
            for s in subjs:

                # skip its parent subjects, already captured above
                if s in g.G.neighbors(o):
                    continue

                # objects cannot flow between characters
                if g.is_character(s) and any([g.is_character(s_) for s_ in g.G.neighbors(o)]):
                    continue

                # li.append((s, None, o))
                li.append((s,
                           CombToken(None, Node('have', 'act')),
                           o))

            # object can have no subject. make the base suggest a subject
            li.append((None, None, o))
            matrix.append(li)

        for comb in itertools.product(*tuple(matrix)):
            # yield list(zip(objs, comb))
            yield self.ravel_comb(comb)

    def ravel_comb(self, triplets_):
        triplets = []
        for t in triplets_:
            if isinstance(t[0], tuple):
                triplets.extend([*t])
            else:
                triplets.append(t)
        return triplets


# do we need to consider <missed subject> under character?

# one problem is that all isolated objects have the same subject MISS
## means they can only be assigned the same object

from more_itertools import set_partitions
from tools.containers import Picture, LayerName

class LayerSlicer:
    def __init__(self):
        pass
        # assert(isinstance(H, GraphSpan))
        # from rules import labels
        # self.subj_dict = labels.subjects
        # self.generator = GraphManipulator(H).get_generator()
        # self.triplet_generator = TripletGenerator(H).get_generator()

    def __call__(self, g):
        assert(isinstance(g, GraphSpan))
        for layers in self.get_layers(g):
            yield Picture.from_layers(layers)

    # def get_generator(self):
    #     for g in self.generator:
    #         # nested_entities = g.get_nested_entities()
    #         # triplet_dict = self.to_triplet_dict(nested_entities)
    #         # for layers in self.get_layers(triplet_dict):
    #         for layers in self.get_layers(g):
    #             yield Picture.from_layers(layers)

#     def to_nested_entities(self, triplets):
#         nested_entities = defaultdict(lambda: defaultdict(set))
#         for n1, v, n2 in triplets:
#             nested_entities[n1][v].add(n2)
#         return ddict2dict(nested_entities)

#     def to_triplet_dict(self, nested_entities):
#         triplet_dict = {'character': [],
#                         'surrounding': [],
#                         'unidentified': []}
#         for key in nested_entities:
#             # if key.keyword.t != MISSED:
#             if key:
#                 if key.keyword.t in self.subj_dict['character']:
#                     triplet_dict['character'].append({key: nested_entities[key]})
#                 elif key.keyword.t in  self.subj_dict['surrounding']:
#                     triplet_dict['surrounding'].append({key: nested_entities[key]})
#                 else:
#                     raise KeyError('Subject not found! %s' % key)
#             else:
#                 triplet_dict['unidentified'].append({key: nested_entities[key]})
#         return triplet_dict

    def merge_tuple(self, tup):
        dic_ = {}
        for dic in tup:
            for key in dic:
                dic_[key] = dic[key].copy()
        return dic_

    # def split_dict(dic):
    #     tup = []
    #     for key in dic:
    #         tup.append({key: dic[key]})
    #     return tuple(tup)

    def get_layers(self, g):
        # each non-character subject form one layer
        dic = g.get_nested_entities_dict()
        fixed_layers = tuple(dic['surrounding'])
        fixed_layers += tuple(dic['unidentified'])

        if not dic['character']:
            yield [LayerName.from_nested_entities(l) for l in fixed_layers]

        # character subjects can be merged into a group
        for n_parts in range(1, len(dic['character'])+1):
            for s in set_partitions(dic['character'], n_parts):
                char_layers = tuple([self.merge_tuple(t) for t in s])
                # yield fixed_layers + char_layers
                yield [LayerName.from_nested_entities(l) for l in (fixed_layers + char_layers)]



# from models.metric import WeightedMeanIOU
from tools.image_process import getSubj
from collections import defaultdict
import itertools
from tools.containers import LayerName, Picture
# from tools.common import enableQuery

# @enableQuery_
# @enableQuery
class LayerGround:
    def __init__(self, vocabbase=None):
        # self.metric = WeightedMeanIOU()
        # self.query = QuerySimi()
        self.base = vocabbase
        self.layer_vocab = vocabbase.layer_vocab_

        self.layer_collocations_ = defaultdict(set)
        for p in vocabbase.pic_vocab_:
            for l1, l2 in itertools.combinations(p.layers_, 2):
                self.layer_collocations_[l1].add(l2)
                self.layer_collocations_[l2].add(l1)

        from rules.labels import subjects
        self.subj_dict = subjects

    def __call__(self, pic):
        """
        Caveats: used vocabbase implicitly
        """
        tups = []
        for layer in pic.layers_:
            tups.append(self.ground(layer))
        layers, simis = zip(*tups)
        # return Picture.from_layers(layers), sum(simis) / len(simis), self.reasonability(layers)
        return Picture.from_layers(layers), max(simis), self.reasonability(layers)

#     def peel_keyword(self, nested_):
#         """
#         peel off keywords in a nested dict of comb tokens
#         """
#         nested = {}
#         for subj in nested_:
#             nested[subj.keyword] = {}
#             for act in nested_[subj]:
#                 nested[subj.keyword][act.keyword] = set()
#                 for obj in nested_[subj][act]:
#                     nested[subj.keyword][act.keyword].add(obj.keyword)
#         return nested

#     def get_categ_base(self, layer):
#         for categ in self.subj_dict:
#             if getSubj(str(layer)) in self.subj_dict[categ]:
#                 return categ
#         raise KeyError('category not found for layer candidates %s' % layer)

    def get_categ(self, layer):
        """
        layer not in the base don't have a string
        """
        # assert(len(list(layer.nested_entities_)) == 1), list(layer.nested_entities_)
        # if multiple keys, that's a group of characters
        for categ in self.subj_dict:
            if list(layer.nested_entities_)[0].t in self.subj_dict[categ]:
                return categ
        return None

    def layer_cands(self, categs):
        if not categs:
            return [l for l in self.layer_vocab]
        return [l for l in self.layer_vocab if l._get_categ() in categs]

    def ravel_layer(self, layer):
        """
        ravel a nested dict to lists of entities
        """
        entities_ = {'subj': [], 'act': [], 'obj': []}
        for subj in layer:
            if subj.t:
                entities_['subj'].append(subj._reset())
            for act in layer[subj]:
                if act.t:
                    entities_['act'].append(act._reset())
                for obj in layer[subj][act]:
                    if obj.t:
                        entities_['obj'].append(obj._reset())
        return entities_


    def jaccard(self, set1_, set2_):
        """
        support duplicate elemenets
        """
        assert(isinstance(set1_, list))
        assert(isinstance(set2_, list))
        if not set1_ or not set2_: return 0

        # set1, set2 = set1_.copy(), set2_.copy()
        set1 = [s for s in set1_ if s]
        set2 = [s for s in set2_ if s]
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

        # set1, set2 = set1_.copy(), set2_.copy()
        set1 = [s for s in set1_ if s]
        set2 = [s for s in set2_ if s]
        inter_simi = []
        while set1 and set2:
            numerate = [(n1, n2, self.base.query_simi(n1.t, n2.t)) for n1 in set1 for n2 in set2]
            # numerate = [(n1, n2, self.query(n1.t, n2.t)) for n1 in set1 for n2 in set2]
            n1_, n2_, simi_ = sorted(numerate, key=lambda x: (x[-1], x[0].count + x[1].count))[-1]
            if simi_ > thresh:
                set1.remove(n1_)
                set2.remove(n2_)
                inter_simi.append(simi_)
            else:
                # the most simi pairs won't pass the threshold
                break
        # simi = sum(inter_simi) / (len(set1_) + len(set2_) - len(inter_simi))
        simi = sum(inter_simi) / (len(set1_) + len(set2_) - sum(inter_simi))
        assert(simi <= 1.0)
        return simi


    def layer_simi(self, layer1_, layer2_):
        """
        layer should be in the form of nested entities
            todo: accept LayerName instance as input
        """
        assert(isinstance(layer1_, LayerName))
        assert(isinstance(layer2_, LayerName))
        layer1 = self.ravel_layer(layer1_.nested_entities_)
        layer2 = self.ravel_layer(layer2_.nested_entities_)

        dic = {'subj': 0.6, # 0.2,
               'act': 0.2,
               'obj': 0.2}
        simi = {'subj': self.jaccard(layer1['subj'],
                                       layer2['subj']),
                'act': self.jaccard_soft(layer1['act'],
                                           layer2['act']),
                'obj': self.jaccard_soft(layer1['obj'],
                                      layer2['obj'])}

        simi['overall'] = dic['subj'] * simi['subj'] + \
                          dic['act'] * simi['act'] +\
                          dic['obj'] * simi['obj']

                          # dic['act'] * simi['act'] + \
        return simi['overall']

    def get_layer_dict(self, layers):
        layer_dict = {'character': set(),
                      'surrounding': set(),
                      'accessory': set(),
                      'background': set()}
        for l in layers:
            layer_dict[l._get_categ()].add(l)
        return layer_dict

    def inter_categ_layer_simi(self, layer1, layer2):
        simis = [self.layer_simi(l, layer2) for l in self.layer_collocations_[layer1] if l._get_categ() == layer2._get_categ()]
        simi12 = max(simis) if simis else 0

        simis = [self.layer_simi(l, layer1) for l in self.layer_collocations_[layer2] if l._get_categ() == layer1._get_categ()]
        simi21 = max(simis) if simis else 0
        # return (simi12 + simi21) / 2
        return max(simi12, simi21)

    def reasonability(self, layers):
        layer_dict = self.get_layer_dict(layers)
        scores = [] # = 0
        for l1 in layer_dict['character']:
            for l2 in layer_dict['surrounding']:
                # score += self.inter_categ_layer_simi(l1, l2)
                scores.append(self.inter_categ_layer_simi(l1, l2))
        # if layer_dict['character'] and layer_dict['surrounding']:
        #    score /= len(layer_dict['character']) * len(layer_dict['surrounding'])
        if scores: return max(scores)
        return 0
        # return score

    def ground(self, layer, top=1):
        tups = []

        ### prevent inventing new characters
        categ = self.get_categ(layer)
        if categ == 'character':
            categs = ['character']
        elif categ == 'surrounding':
            categs = ['background', 'accessory', 'surrounding']
        elif not categ:
            categs = ['background', 'accessory', 'surrounding']
        else:
            raise KeyError

        for layer_ in self.layer_cands(categs=categs):
            tups.append((layer_, self.layer_simi(layer, layer_)))
        if top > 1:
            return sorted(tups, key=lambda x: x[1])[::-1][:top]
        return sorted(tups, key=lambda x: x[1])[-1]

