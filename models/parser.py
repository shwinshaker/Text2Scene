#!./env python

import spacy
from spacy.matcher import Matcher
import networkx as nx
import itertools
import re
from collections import defaultdict
import warnings

from rules.consts import MISSED, UNK
from tools.containers import LayerName, Picture, Node
from tools.common import ddict2dict

class GraphParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def get_verb_phrase(self):
        """
        self-defined verb phrase matcher
        """
        matcher = Matcher(self.doc.vocab)
        pattern = [{"POS": "VERB"},
                   {"POS": {"IN": ["ADV","ADP","PART"]}, "OP": "*"}]
        matcher.add("Verb Phrase:", None, pattern)
        phrases = []
        for _, start, end in matcher(self.doc):
            phrase = self.doc[start:end]
            # remove single stop words such as 'is' 'are'
            if len(phrase) == 1:
                if phrase[0].is_stop:
                    continue

            # greedy match
            same_roots = [p for p in phrases if p.root == phrase.root]
            if same_roots:
                # there two phrase refering to same verb root. E.g. "sit on" and "sit"
                assert(len(same_roots) == 1)
                p_ = same_roots[0]
                if len(p_) < len(phrase):
                    # choose the longer one
                    phrases.remove(p_)
                    phrases.append(phrase)
            else:
                phrases.append(phrase)
        return phrases

    def get_noun_phrase(self):
        """
        use internal noun phrase matcher
        """
        return list(self.doc.noun_chunks)

    def is_connect(self, nop, vp):
        """
        check if a noun phrase and a verb phrase is connected
        """
        for v in vp:
            # check if two are directly connected in the dependency tree
            if nop.root.head == v or v.head == nop.root:
                return nop.root.dep_
        #   this allow verbs to be reused, move to the end of the pipeline
        #     for c in np.conjuncts:
        #         if c.head == v:
        #             return c.dep_[1:]
        for v in vp.conjuncts:
            # conjuctions of verb can be connected to a noun phrase.
            # E.g. A is doing and making ...
            if nop.root.head == v or v.head == nop.root:
                # only allow subjects propagrate through
                #  E.g. A is doing B and making C.
                # C and doing shouldn't connect.
                if re.match(r'\D*subj\D*', nop.root.dep_):
                    return nop.root.dep_
        return None

    def to_subj_or_obj(self, dep, n, v):
        """
        translate tags in dependency tree to subject | object
            But this may not be correct in case of passive voice
        """
        if not dep: return None
        if re.match(r'\D*subj\D*', dep): return 'subj'
        if re.match(r'\D*obj\D*', dep): return 'obj'
        warnings.warn('Unexpected dependency tag! %s between %s and %s' % (dep, n, v))
        # raise ValueError('Unexpected dependency tag! %s' % dep, n, v)
        return None

    def is_SVO(self, n1, n2, v):
        """
        determine the connection is valid in a subj-verb-obj form
            two connected subjects or two connected objs are invalid.
                ! E.g. a man and a boy are playing computer.
                    "man" and "boy" are not connected.
        """
        conns = [self.to_subj_or_obj(self.is_connect(n1, v), n1, v),
                 self.to_subj_or_obj(self.is_connect(n2, v), n2, v)]
        conns = [c for c in conns if c]
        # only if subj and obj occur together, SVO stands
        # which means conns contains different tags
        if len(set(conns)) == 2:
        # if len(conns) == 2:
            return True
        return False

    def is_reverse(self, n1, n2):
        """
        if the leading noun is in passive voice, exchange them
        """
        # n1 must be the leading token
        assert(n1.root.i <= n2.root.i), (n1, n2)
        if re.match(r'\D*pass$', n1.root.dep_): return True
        if re.match(r'\D*subj\D*', n2.root.dep_):
            if re.match(r'\D*obj\D*', n1.root.dep_):
                return True
        return False

    def conjunts_expand(self, conns, nps):
        """
        The conjunctions of nouns share the same verbs and objects
        E.g. "A man and a boy are playing computer."
            boy will be conjuncted to man
        """
        conns_c = []
        for n1, n2, dic in conns:
            for c in n1.conjuncts:
                for n_ in nps:
                    if c in n_:
                        conns_c.append((n_, n2, dic))
            for c in n2.conjuncts:
                for n_ in nps:
                    if c in n_:
                        conns_c.append((n1, n_, dic))
        conns.extend(conns_c)
        return conns

    def get_edges(self, nouns, verbs):
        """
        if passive, needs to rectify the order
        Given nouns and verbs, infer connections in between
        """
        connections = []
        # nouns_ = nouns.copy()
        _verbs = []
        for n1, n2 in itertools.combinations(nouns, 2):
            for v in verbs:
                if self.is_SVO(n1, n2, v):
                    if self.is_reverse(n1, n2):
                        n1, n2 = n2, n1
                    connections.append((n1, n2, {'verb': v}))
                    # connections.append((n1, n2, v))
                    _verbs.append(v)
                    # if n1 in nouns_: nouns_.remove(n1)
                    # if n2 in nouns_: nouns_.remove(n2)
        self.conjunts_expand(connections, nouns)
        return connections, [v for v in verbs if v not in _verbs] #, nouns_

    def append_verbs(self, verbs, nouns):
        """
        absorb verbs with no subject or object
        """
        # print(verbs, nouns)
        noun_comps = []
        _verbs = []
        for v in verbs:
            for n in nouns:
                # if n.root.text == 'alien': print(n,v)
                # print(v)
                if self.is_connect(n, v):
                # if n.root in v.root.children:
                    # print(n,v)
                    noun_comps.append((n, {'verb': v}))
                    # noun_comps.append((n, v))
                    _verbs.append(v)
        return noun_comps, [v for v in verbs if v not in _verbs]

    def __call__(self, text):
        # parse text
        self.doc = self.nlp(text)
        self.nouns_ = self.get_noun_phrase()
        self.verbs_ = self.get_verb_phrase()
        self.edges_, self.rest_verbs_ = self.get_edges(self.nouns_,
                                                       self.verbs_)
        # self.noun_comps_, self.rest_verbs_ = self.append_verbs(self.rest_verbs_, self.nouns_)
        self.noun_comps_, _ = self.append_verbs(self.verbs_, self.nouns_)

        # generate graph
        self.G = nx.Graph()
        self.G.add_nodes_from(self.nouns_)
        self.G.add_nodes_from(self.noun_comps_)
        self.G.add_edges_from(self.edges_)
        self.G = nx.freeze(self.G)
        assert(nx.is_frozen(self.G))

        return self.G

    # def plot(self, style='networkx', **kwargs):
    #     if style == 'networkx':
    #         self.plot_network(**kwargs)
    #     elif style == 'layername':
    #         self.plot_triplets(**kwargs)
    #     else:
    #         raise KeyError('Available style: networkx and layername')

    # def plot_network(self, edge=False):
    #     """
    #     Use networkx's graph plot
    #     """
    #     nx.draw(self.G, with_labels=True,
    #             font_weight='bold', node_size=50)

    #     if edge:
    #         pos = nx.spring_layout(self.G)
    #         # nx.draw_networkx_nodes(G, pos=pos, node_size=50)
    #         # nx.draw_networkx_labels(G, pos=pos)
    #         # nx.draw_networkx_edges(G, pos=pos, edge_color='k', width=1)
    #         edge_labels = nx.get_edge_attributes(self.G,'verb')
    #         nx.draw_networkx_edge_labels(self.G, pos=pos,
    #                                      edge_labels=edge_labels)

    # def get_triplets(self):
    #     triple_set = [(n1, e, n2) for n1, n2, e in self.G.edges(data='verb')]
    #     entity_set = [(n, a, None) for n, a in self.G.nodes(data='verb')]
    #     return triple_set + entity_set

    # def plot_triplets(self, collapse=False):
    #     """
    #     call layerName.plot to plot triplets
    #     """
    #     def to_node(span, attr, reset=False):
    #         if not span:
    #             return Node(MISSED, attr=attr)
    #         i = i=span.root.i
    #         if reset: i = 0
    #         return Node(span.root.lemma_, i=i, attr=attr)
    #         # return Node(span.root.lemma_, i=0, attr=attr, count=1)

    # #     def get_keyword(n):
    # #         # if not n: return None
    # #         assert(n.keyword), n
    # #         return n.keyword

    #     def to_nested_entities(triplets):
    #         nested_entities = defaultdict(lambda: defaultdict(set))
    #         for n1, v, n2 in triplets:
    #             nested_entities[to_node(n1, 'subj')][to_node(v, 'act')].add(to_node(n2, 'obj'))
    #         return ddict2dict(nested_entities)

    #     if not collapse:
    #         nested_entities = to_nested_entities(self.get_triplets())
    #         layer = LayerName.from_nested_entities(nested_entities)
    #         layer.plot()
    #     else:
    #         # layer = LayerName
    #         layers = []
    #         for n1, v, n2 in self.get_triplets():
    #             nested_entities = defaultdict(lambda: defaultdict(set))
    #             nested_entities[to_node(n1, 'subj', reset=True)][to_node(v, 'act', reset=True)].add(to_node(n2, 'obj', reset=True))
    #             layer = LayerName.from_nested_entities(ddict2dict(nested_entities))
    #             # print(layer.nested_entities_)
    #             layers.append(layer)
    #         picture = Picture.from_layers(layers)
    #         picture.plot()
