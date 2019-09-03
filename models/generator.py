#!./env python

from tools.knowledge import LayerBase
from rules.labels import subjects
from tools.image_process import getSubj
from tools.containers import Picture

import itertools
import random

# the frequency should be based on priors
def exhaustivePicGenerator(layerbase, beam={'background': 2,
                                            'surrounding': 10,
                                            'character': 10,
                                            'accessory': 2}, verbose=True):
    # layerbase = LayerBase()

    comb_dic = {}
    comb_dic['background'] = ['#background', '']
    comb_dic['surrounding'] = [str(l) for l in layerbase.layer_vocab_ if getSubj(str(l)) in subjects['surrounding']] + ['']
    comb_dic['character'] = [str(l) for l in layerbase.layer_vocab_ if getSubj(str(l)) in subjects['character']] + ['']
    comb_dic['accessory'] = [str(l) for l in layerbase.layer_vocab_ if getSubj(str(l)) == 'accessory'] + ['']
    # comb_dic['accessory'] = ['#accessory', '']

    li = []
    for key in comb_dic:
        assert(beam[key] <= len(comb_dic[key])), (beam[key], len(comb_dic[key]))
        layers_ = comb_dic[key].copy()
        random.shuffle(layers_)
        li.append(layers_[:beam[key]])

    # combs = list(itertools.product(*tuple(comb_dic.values())))
    combs = list(itertools.product(*tuple(li)))

    if verbose:
        for categ in comb_dic:
            print(categ, len(comb_dic[categ]))
        print('combs', len(combs))

    def to_list_of_layernames(tup):
        return [t for t in tup if t]

    for i, t in enumerate(combs):
        print('[%i]' % i, end='\r')
        layernames = to_list_of_layernames(t)
        if layernames:
            yield Picture(layernames=layernames)


import networkx as nx
import itertools
from tools.instance import Node, CombToken
from rules.consts import MISSED

class TripletGenerator:
    """
    accepts a graph, return a triplet combination generator
    allow the flow of weakly connected objects
    """

    def __init__(self, G):
        assert(isinstance(G, nx.classes.graph.Graph))
        self.G = G

        from rules import labels
        self.subj_dict = labels.subjects

    def get_generator(self):
        fixed_set = self.get_triples(strong_only=True)

        for weak_comb in self.get_weak_triples():
            # comb_set = [self.rectify(*tup) for tup in self.ravel_comb(weak_comb)]
            comb_set = [self.rectify(*tup) for tup in weak_comb]
            yield comb_set + fixed_set

    def is_strong(self, n1, n2):
        return self.G[n1][n2]['intension'] > 0.5

    def is_weakly_connected(self, n):
        for n_ in self.G.neighbors(n):
            if self.is_strong(n_, n):
                return False
        return True

    def is_subj(self, n):
        return n.keyword.attr == 'subj'

    def is_obj(self, n):
        return n.keyword.attr == 'obj'

    # def get_weak_objs(self):

    def get_weak_triples(self):
        subjs = [cn for cn in self.G.nodes if self.is_subj(cn)]
        objs = [cn for cn in self.G.nodes if self.is_obj(cn) and self.is_weakly_connected(cn)]
        # print('subjs: ', subjs)
        # print('flexible objs: ', objs)

        matrix = []
        for o in objs:
            li = []
            # first add the orignial weakly connected triplets as a possibility
            ## object connected to multiple subjects should be considered simutaneously
            all_weaks = []
            for s in self.G.neighbors(o):
                if not self.is_strong(s, o) and self.is_subj(s):
                    all_weaks.append((s, self.G[s][o]['verb'], o))
            if all_weaks:
                li.append(tuple(all_weaks))

            # then for each other non-neighour subjects, try bind this object to
            for s in subjs:

                # skip its parent subjects, already captured above
                if s in self.G.neighbors(o):
                    continue

                # objects cannot flow between characters
                if any([s_.keyword.t in self.subj_dict['character'] for s_ in self.G.neighbors(o)]) and s.keyword.t in self.subj_dict['character']:
                    continue

                li.append((s, None, o))

            # object can have no subject. make the base suggest a subject
            li.append((None, None, o))
            matrix.append(li)

        for comb in itertools.product(*tuple(matrix)):
            # yield list(zip(objs, comb))
            yield self.ravel_comb(comb)

    def reorder(self, n1, e, n2):
        """
        reorder the triplet such that the first is always a subject
            and better be a character if a deuce
        """
        if n1 and n2:
            # if both subjects, make sure n1 is character
            if self.is_subj(n1) and self.is_subj(n2):
                if n2.keyword.t in self.subj_dict['character']:
                    return (n2, e, n1)
            if self.is_obj(n1):
                assert(self.is_subj(n2)), n2
                return (n2, e, n1)
            # this to make sure only n1 will be checked
            # if n1 and n2 are both subjects, e.g. bear -> wild accidentally
            # then keep the order
            return (n1, e, n2)
        if n1:
            if self.is_obj(n1):
                return (n2, e, n1)
            return (n1, e, n2)
        # only explicitly check n2 when n1 is None
        if n2:
            if self.is_subj(n2):
                return (n2, e, n1)
        return (n1, e, n2)

    def filter_none(self, tup):
        tup_ = []
        for c, attr in zip(tup, ['subj', 'act', 'obj']):
            tup_.append(c if c else CombToken(None, Node(MISSED, attr=attr)))
        return tuple(tup_)

    def rectify(self, n1, e, n2):
        return self.filter_none(self.reorder(n1, e, n2))

    def ravel_comb(self, triplets_):
        triplets = []
        for t in triplets_:
            if isinstance(t[0], tuple):
                triplets.extend([*t])
            else:
                triplets.append(t)
        return triplets

    def get_triples(self, strong_only=False):

        ## all the edges, i.e. triplets
        if strong_only:
            triple_set = [self.rectify(n1, e, n2) for n1, n2, e in self.G.edges(data='verb') if self.is_strong(n1, n2)]
        else:
            triple_set = [self.rectify(n1, e, n2) for n1, n2, e in self.G.edges(data='verb')]

        ## all the entities along with their associated verbs
        entity_set = [self.rectify(n, a, None) for n, a in self.G.nodes(data='verb')]
        return triple_set + entity_set
