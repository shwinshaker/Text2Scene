#!./env python

from .image_process import getLayerNames, checkLayerName
from .text_process import SpacyLemmaTokenizer, SimpleLemmaTokenizer
# from .common import ravel
import copy
import warnings

class Picture:

    @staticmethod
    def from_layers(layers):
        assert(isinstance(layers[0], LayerName))
        picture = Picture()
        picture.layers_ = layers
        picture.layernames_ = [l.s for l in layers]
        picture.triple_set_ = set([layer.triples_ for layer in layers])
        return picture

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
            self.layernames_ = layernames

        if self.layernames_:
            self.layer_merge_ = LayerName(src=self.img_name)
            self.layers_ = []
            for layername in self.layernames_:
                layer = LayerName(layername, src=self.img_name)
                self.layers_.append(layer)
                self.layer_merge_.absorb(layer)
            # make the layers immutable
            self.layers_ = tuple(self.layers_)
            self.plot = self.layer_merge_.plot

            # vocab is a set, no duplicates
            self.vocab_ = self.layer_merge_._ravel(self.layer_merge_.nested_entities_)

            self.triple_set_ = set([layer.triples_ for layer in self.layers_])

    def __repr__(self):
        """
        used to print a string when directly call the object?
        also used to compare if two pictures are same. same as __eq__?
        """
        return '; '.join(self.layernames_)

    def __lt__(self, other):
        return self.__repr__() < other.__repr__()

    def __eq__(self, other):
        # should consider overlapping order here?
        # but it should make no difference if ravel the keywords as features
        # lets omit it for now
        # ! the order of layers doesn't matter
        return self.triple_set_ == other.triple_set_

    def __hash__(self):
        return hash(tuple(self.triple_set_))

    def __len__(self):
        return len(self.layers_)

    def __iter__(self):
        return iter(self.layers_)


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

        # tokenizer = SpacyLemmaTokenizer()
        tokenizer = SimpleLemmaTokenizer()
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


from tools.instance import Node
from tools.common import absorbNestedDict, ddict2dict
import re
from collections import defaultdict

class LayerName:
    @staticmethod
    def from_nested_entities(nested_entities):
        assert(isinstance(nested_entities_, dict))
        layer = LayerName()
        layer.nested_entities_ = nested_entities
        layer.entities_ = layer._get_entities()
        layer.triples_ = layer._get_triples()
        return layer

    """
    given layer Name, return nested entities list
    E.g. subj(act[obj]) -> {'subj': {'act': ['obj']}}
        Caveats:
            - when absorb called collapse, nested_entities_ contains no count information but entities_ does, thus if call _get_entities again, these two entities diverge
            -- should include count information in nested_entities_

    """
    def __init__(self, s='', src=None):
        assert(isinstance(s, str)), s
        if s: checkLayerName(s)

        self.s = s
        self.src = src # source picture
#         self.obj_ptn = '\[\w+(?=,\w+)*\]'
#         self.act_obj_ptn = '\w+(?=%s)?' % self.obj_ptn

        if not self.s:
            self.nested_entities_ = {}
            self.entities_= {'subj': {}, 'act': {}, 'obj': {}}
        else:
            self.nested_entities_ = self._get_nested_entities()
            self.entities_ = self._get_entities()
        self.triples_ = self._get_triples()

    def __eq__(self, other):
        """
        nested entities are same or triples are same
        """
        return self.nested_entities_ == other.nested_entities_

    def __lt__(self, other):
        return self.s < other.s

    def __hash__(self):
        return hash(self.triples_)

    def __repr__(self):
        return self.s

    def _ravel(self, nested_entities_):
        ravel_ = set()
        for subj in nested_entities_:
            ravel_.add(subj)
            for act in nested_entities_[subj]:
                ravel_.add(act)
                for obj in nested_entities_[subj][act]:
                    ravel_.add(obj)
        return ravel_

    def __individualize_subjs(self, s):
        """
        if there are mutiple same subjects in a layer, name them sequencially
            E.g. man(),man() -> man1(),man2()
        """
        subjs = re.findall('[\[|,](\w+)\(', s)
        if len(subjs) != len(set(subjs)):
            duplicates = list(set([subj for subj in subjs if subjs.count(subj)>1]))
            for subj in duplicates:
                for i in range(subjs.count(subj)):
                    ## substitute orignial name
                    s = re.sub('(?<=[\[,])%s(?=\()' % subj,
                               '%s%i' % (subj, i+1), s, count=1)
        return s

    def _get_subjs(self):
        """
        define a exclusion variable to determine if resolve conflict
            same variable used by get_nested_subjs
        """
        # serialize name for later associated action detection
        self.__s = self.__individualize_subjs(self.s)

        if self.__s.startswith('#background'):
            # return ['background']
            return [Node('background', attr='subj')]
        if self.__s.startswith('#accessory'):
            # return ['accessory']
            return [Node('accessory', attr='subj')]
        if self.__s.startswith('#group'):
            # action can not be neglected, thus here we can append \(
            # but if actions can be neglected, need to modify here


            subjs = re.findall('[\[|,](\w+)\(', self.__s)
            # subjs_ = [] # temp list for count
            nodes = []
            for subj in subjs:
                if re.match(r'\D+\d+', subj):
                    reg = re.findall(r'(\D+)(\d+)', subj)
                    assert(len(reg) == 1)
                    reg_ = reg[0]
                    # nodes.append(Node(subj, i=subjs_.count(subj), attr='subj'))
                    nodes.append(Node(reg_[0], i=int(reg_[1]), attr='subj'))
                else:
                    nodes.append(Node(subj, attr='subj'))
                    # subjs_.append(subj)
                    # subjs_.append(subj)
            assert(len(nodes) == len(set(nodes)))
            return nodes
        else:
            subjs = re.findall('^#(\w+)\(', self.__s)
            assert len(subjs) == 1, (self.__s, subjs)
            return [Node(subjs[0], attr='subj')]
        # # make sure there are no duplicated subjects
        # assert(len(subjs) == len(set(subjs)))
        # return subjs

    def _get_acts(self):
        """
        given subj, find associated actions
            what if subjs are same? E.g. there are two man in the same layer!!
        """
        subjs = self._get_subjs()
        # if group, remove group mark
        if self.__s.startswith('#group'):
            s = re.sub('#group\(have', '', self.__s)
            s = s.rstrip(')')
        else:
            # make the form consistent
            s = '[%s]' % self.__s.lstrip('#')

        # temporarily remove all objects
        obj = '\[\w+(,\w+)*\]'
        s = re.sub(obj, '', s)

        # extend or append
        # acts = defaultdict(list)
        acts = defaultdict(set)
        for subj in subjs:
            if subj not in acts:
                acts[subj] = set() # []
            for act in re.findall(r'[\[,]{subj}\(([\w,]+)\)'.format(subj=subj), s):
                if ',' in act:
                    # acts[subj] |= set(act.split(','))
                    acts[subj] |= set([Node(a, attr='act') for a in act.split(',')])
                else:
                    # acts[subj].append(act)
                    # acts[subj].add(act)
                    acts[subj].add(Node(act, attr='act'))
        return ddict2dict(acts)

    def _get_nested_entities(self):
        """
        given subj, actions,  find associated objects
        """
        # if not self.s:
            # return defaultdict(lambda: defaultdict(set))
            # return {}
            # return defaultdict(lambda: defaultdict(list))
            # defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        acts = self._get_acts()

        # if group, remove group mark
        if self.__s.startswith('#group'):
            s = re.sub('#group\(have', '', self.__s)
            s = s.rstrip(')')
        else:
            s = '[%s]' % self.__s.lstrip('#')

        # extend or append
        objs = defaultdict(lambda: defaultdict(set))
        # objs = defaultdict(lambda: defaultdict(list))
        for subj in acts:
            if subj not in objs:
                objs[subj] = {}
            for act in acts[subj]:
                if act not in objs[subj]:
                    objs[subj][act] = set() # []
                    # objs[subj][act] = {}
                regex = r'[\[,]{subj}\([\w,\[\]]*{act}\[([\w,]+)\][\w,\[\]]*\)[\],]'.format(subj=subj, act=act)
                for obj in re.findall(regex, s):
                    if obj:
                        if ',' in obj:
                            # objs[subj][act].extend(obj.split(','))
                            # objs[subj][act] |= set(obj.split(','))
                            objs[subj][act] |= set([Node(o, attr='obj') for o in obj.split(',')])
                        else:
                            # objs[subj][act].append(obj)
                            # objs[subj][act].add(obj)
                            objs[subj][act].add(Node(obj, attr='obj'))

        return ddict2dict(objs)

    def _get_entities(self):
        """
        a dictionary of all the entities list
            todo: need to resolve multiple subjects, because get_subjs resolve conflicts
        """

        entities = defaultdict(lambda: defaultdict(int))
        for subj in self.nested_entities_:
            assert(subj not in entities['subj']), subj
            entities['subj'][subj] += subj.count #.add(subj)
            for act in self.nested_entities_[subj]:
                # same actions in different subject will be counted separately
                entities['act'][act] += act.count #.add(act)
                for obj in self.nested_entities_[subj][act]:
                    entities['obj'][obj] += obj.count #.add(obj)
        return ddict2dict(entities)

    def _get_triples(self):
        """
        a tuple of all the triples in the layer
            If two layers have same nested entities,
            then they have same triples list,
            which means they are literally the same
        """
        triples_ = []
        for subj in self.nested_entities_:
            if not self.nested_entities_[subj]:
                triples_.append((subj,))
            for act in self.nested_entities_[subj]:
                if not self.nested_entities_[subj][act]:
                    triples_.append((subj, act))
                for obj in self.nested_entities_[subj][act]:
                    triples_.append((subj, act, obj))
        return tuple(triples_)

    def absorb(self, other_, subj_exclusion=False):
        """
        absorb other layers into this layer, merge entities accordingly
        """

        if not other_.nested_entities_:
            raise RuntimeError('Can not absorb an empty layer!')

        # merge nested entites
        if not subj_exclusion:

            # merge man1 and man2
            self.collapse_subj()
            # this does the trouble, shouldn't change the one that is absorbed
            other = copy.deepcopy(other_)
            other.collapse_subj()
            absorbNestedDict(self.nested_entities_,
                             other.nested_entities_)

        else:
            """
            now are using dict of dict of set, may should do some modification here
                todo: modify this part since we now introduce the id and count of node
                      simply add the key because id are exclusive
            """
            raise NotImplementedError('Exclusion absorption needs recheck')
            for subj in other.nested_entities_:
                sub = re.sub(r'\d*$','',subj)
                if sub not in self.nested_entities_:
                    self.nested_entities_[subj] = other.nested_entities_[subj]
                else:
                    count = 0
                    for subj_ in self.nested_entities_:
                        if re.match('^{subj}\d*$'.format(subj=sub), subj_):
                            count += 1
                    self.nested_entities_['%s%i' % (sub, count+1)] = other.nested_entities_[subj]

        # # merge entities
        # # show new entities list
        # # self.entities_ = self.__get_entities()
        # for type_ in other.entities_:
        #     assert(type_ in self.entities_), (type_, self.entities_.keys())
        #     for entity in other.entities_[type_]:
        #         if entity not in self.entities_[type_]:
        #             self.entities_[type_][entity] = 0
        #         self.entities_[type_][entity] += other.entities_[type_][entity]
        # # self.entities_ = ddict2dict(self.entities_)

        # ----------
        # Aug 17: now we incorporate count information into nested_entities_
        #         other variables can simply re-gen
        #         means only need to maintain one variable
        # -----------
        # regenerate entities
        self.entities_ = self._get_entities()

        # regenerate tuples
        self.triples_ = self._get_triples()

    def collapse_subj(self):
        """
        collapse subjk such that we no longer label two men in one layer separately
            # todo: the right way is to add count when merge subjects
            #       then no need to explicitly merge entities_
        """
        def __count_dups(sub):
            return [n._reset() for n in self.nested_entities_].count(sub)

        # collapse nested dict
        # nested_entities_clps_ = defaultdict(lambda: defaultdict(list))
        nested_entities_clps_ = defaultdict(lambda: defaultdict(set))
        for subj in self.nested_entities_:
            if subj.i > 0:
                sub = subj._reset()
                sub.count = __count_dups(sub) # add count
                absorbNestedDict(nested_entities_clps_[sub],
                                 self.nested_entities_[subj])
            else:
                nested_entities_clps_[subj] = self.nested_entities_[subj]
        self.nested_entities_ = ddict2dict(nested_entities_clps_)

        # regenerate triples
        self.triples_ = self._get_triples()

        # regenrate entities
        self.entities_ = self._get_entities()

        # # collapse dict, such that count are summed
        # entities_clps_ = defaultdict(lambda: defaultdict(int))
        # entities_clps_['subj'] = defaultdict(int)
        # entities_clps_['act'] = defaultdict(int)
        # entities_clps_['obj'] = defaultdict(int)
        # for type_ in self.entities_:
        #     for entity in self.entities_[type_]:
        #         # if re.match(r'^\w+\d+$', entity):
        #         #     sub = re.sub(r'\d*$', '', entity)
        #         if entity.i > 0:
        #             sub = entity._reset()
        #             entities_clps_[type_][sub] += self.entities_[type_][entity]
        #         else:
        #             entities_clps_[type_][entity] = self.entities_[type_][entity]
        # self.entities_ = ddict2dict(entities_clps_)

    def ravel(self):
        """
            ravel a layer to a tuple of keywords (weighted)
                what to do with keyword occurring more than once
        """
        pass
        return tuple()

    def print_(self):
        print(self.triples_)
        # for subj in self.nested_entities_:
        #     if not self.nested_entities_[subj]:
        #         print('%s(subj)' % subj)
        #     for act in self.nested_entities_[subj]:
        #         if not self.nested_entities_[subj][act]:
        #             print('%s(subj) - %s(act)' % (subj, act))
        #         for obj in self.nested_entities_[subj][act]:
        #             print('%s(subj) - %s(act) - %s(obj)' % (subj, act, obj))

    def plot(self, save_fig=False):

        # regain entities, because merge entities are sets
        # entities_ = self._get_entities()
        entities_ = self.entities_

        len_subj = len(entities_['subj'])
        len_act = len(entities_['act'])
        len_obj = len(entities_['obj'])

        import matplotlib.pyplot as plt
        figsize = (5, max(len_subj, len_act, len_obj)/6*2)
        plt.figure(figsize=figsize)
        plt.plot([1]*len_subj, range(len_subj),'r.')
        plt.plot([2]*len_act, range(len_act),'g.')
        plt.plot([3]*len_obj, range(len_obj), '.', color='orange')

        def atoi(text):
            return int(text) if text.isdigit() else text

        def natural_keys(text):
            '''
            alist.sort(key=natural_keys) sorts in human order
            http://nedbatchelder.com/blog/200712/human_sorting.html
            (See Toothy's implementation in the comments)
            '''
            return [ atoi(c) for c in re.split(r'(\d+)', text.t) ]

        def get_xy(t, attr):
            if attr == 'subj':
                return (1, sorted(list(entities_['subj']),
                                  key=natural_keys).index(t))
            elif attr == 'act':
                return (2, sorted(list(entities_['act']),
                                  key=natural_keys).index(t))
            elif attr == 'obj':
                return (3, sorted(list(entities_['obj']),
                                  key=natural_keys).index(t))
            else:
                raise KeyError(attr)

        for subj in self.nested_entities_:
            for act in self.nested_entities_[subj]:
                if act.t != 'have':
                    xs, ys = list(zip(get_xy(subj, 'subj'), get_xy(act, 'act')))
                    plt.plot(xs, ys, 'k-', alpha=0.1)
                    for obj in self.nested_entities_[subj][act]:
                        xs, ys = list(zip(get_xy(act, 'act'), get_xy(obj, 'obj')))
                        plt.plot(xs, ys, 'k-', alpha=0.1)
                else:
                    for obj in self.nested_entities_[subj][act]:
                        xs, ys = list(zip(get_xy(subj, 'subj'), get_xy(obj, 'obj')))
                        plt.plot(xs, ys, 'k:', alpha=0.1)

        for i, subj in enumerate(sorted(list(entities_['subj']),
                                        key=natural_keys)):
            plt.text(1, i, '%s(%i)' % (subj, self.entities_['subj'][subj]), color='r')
        for i, act in enumerate(sorted(list(entities_['act']),
                                       key=natural_keys)):
            plt.text(2, i, '%s(%i)' % (act, self.entities_['act'][act]), color='g')
        for i, obj in enumerate(sorted(list(entities_['obj']),
                                       key=natural_keys)):
            plt.text(3, i, '%s(%i)' % (obj, self.entities_['obj'][obj]), color='orange')
        plt.axis('off')
        if save_fig:
            plt.savefig('results/graph', bbox_inches='tight')
        # plt.show()

