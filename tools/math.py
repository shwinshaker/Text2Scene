#!./env python

import numpy as np

class Normalizer():
    """
    A transformer used for standard normalization
    """
    def __init__(self):
        pass

    def fit(self, x):
        self.mean = np.mean(x)
        self.std = np.std(x)

    def transform(self, x):
        return (x - self.mean) / self.std

def sigmoid(x):
    return 1/(1+np.exp(-x))

class Node:
    def __init__(self, t, attr):
        self.t = t
        self.attr = attr
        self.count = 1
        self.neighbors = []

    def __str__(self):
        return '%s(%s)' % (self.t, self.attr)

    def __eq__(self, other):
        """
        must implement this to support comparation between nodes
        """
        if not isinstance(other, Node):
            raise TypeError(other)
        return self.t == other.t and self.attr == other.attr

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        """
        need to explicitly implement hash function to make it hashable if __eq__ is implemented
        seems to recommend xor.
           see. https://stackoverflow.com/questions/4005318/how-to-implement-a-good-hash-function-in-python
                https://stackoverflow.com/questions/2909106/whats-a-correct-and-good-way-to-implement-hash
        """
        return hash((self.t, self.attr))

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

            # get all the nodes and edges
            self.subjs_ = self.subjs()
            self.acts_ = self.acts()
            self.objs_ = self.objs()
            self.edges_ = set() # Edges()
            self.nodes_ = set()

            for subj in self.subjs_:
                self.nodes_.add(Node(subj, 'subj'))
                for act in self.acts_:
                    if self.is_connect_subj_act(subj, act):
                        self.edges_.add((Node(subj, 'subj'), Node(act, 'act')))
            for obj in self.objs_:
                # assume that repetitive objects refer to the same one
                #        when instantiate from a layer name
                #        thus no need to check duplicate
                self.nodes_.add(Node(obj, 'obj'))
                for subj in self.subjs_:
                    if self.is_connect_subj_obj(subj, obj):
                        self.edges_.add((Node(subj, 'subj'), Node(obj, 'obj')))
            for act in self.acts_:
                self.nodes_.add(Node(act, 'act'))
                for obj in self.objs_:
                    if self.is_connect_act_obj(act, obj):
                        self.edges_.add((Node(act, 'act'), Node(obj, 'obj')))

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

    def acts(self):
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
        acts = []
        for act in re.findall(r'\((.*?)\)', s):
            if ',' in act:
                acts.extend(act.split(','))
            else:
                acts.append(act)

        return set(acts)

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
        a problem will happen if a word can either be verb and noun
            better indicate attribute when query
        """
        if (self.to_node(t1), self.to_node(t2)) in self.edges_:
            return True
        else:
            return (self.to_node(t2), self.to_node(t1)) in self.edges_

#         if t1 in self.subjs_:
#             if t2 in self.objs_:
#                 return self.is_connect_subj_obj(t1, t2)
#             elif t2 in self.acts_:
#                 return self.is_connect_subj_act(t1, t2)
#             elif t2 in self.subjs_:
#                 raise AttributeError('%s and %s are both subjects!' % (t1, t2))
#             else:
#                 raise KeyError('%s not found!' % t2)
#         elif t1 in self.acts_:
#             if t2 in self.objs_:
#                 return self.is_connect_act_obj(t1, t2)
#             elif t2 in self.subjs_:
#                 return self.is_connect_subj_act(t2, t1)
#             elif t2 in self.acts_:
#                 raise AttributeError('%s and %s are both actions!' % (t1, t2))
#             else:
#                 raise KeyError('%s not found!' % t2)
#         elif t1 in self.objs_:
#             if t2 in self.acts_:
#                 return self.is_connect_act_obj(t2, t1)
#             elif t2 in self.subjs_:
#                 return self.is_connect_subj_obj(t2, t1)
#             elif t2 in self.objs_:
#                 raise AttributeError('%s and %s are both objects!' % (t1, t2))
#             else:
#                 raise KeyError('%s not found!' % t2)
#         else:
#             raise KeyError('%s not found!' % t1)

    # @staticmethod
    def is_connect_subj_obj(self, subj, obj):
        obj_pat = '\[\w+(,\w+)*\]'
        act_obj_pat = '\w+(%s)*' % obj_pat
        if re.match(r'.*?%s\((%s,)*\w+\[(\w+,)*%s(,\w+)*\](,%s)*\).*?' % (subj, act_obj_pat, obj, act_obj_pat), self.s):
            return True
        return False

    # @staticmethod
    def is_connect_act_obj(self, act, obj):
        if re.match(r'.*?%s\[(\w+,)*%s(,\w+)*\].*?' % (act, obj), self.s):
            return True
        return False

    # @staticmethod
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
