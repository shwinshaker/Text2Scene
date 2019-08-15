#!./env python

import re
from xml.dom.minidom import parse
from collections import defaultdict
from tools.common import absorbNestedDict

def dict_ai2puncs_():
    dic = {}
    dic['_x23_'] = '#'
    dic['_x28_'] = '('
    dic['_x29_'] = ')'
    dic['_x5B_'] = '['
    dic['_x5D_'] = ']'
    dic['_x2C_'] = ','
    dic['_x5F_'] = '-'
    return dic

def cleanName(s):
    s = multiple_replace(dict_ai2puncs_(), s)
    s = re.sub('_x?\d+_', '', s) # remove other symbols
    s = re.sub('_', '', s) # remove _  (space)

    return re.sub('-', '_', s) # replace - back to _

def multiple_replace(dic, text):
    """
    mutiple regex substitutions
        Bug: keys that are prefixes of other keys will break
    """
    # Create a regular expression  from the dictionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape,
                                             dic.keys())))

    # For each match, look-up corresponding value in dictionary
    return regex.sub(lambda mo:
                     dic[mo.string[mo.start():mo.end()]],
                     text)

def rectifyLayer(path, li):
    """
    something to do to rectify the layer order to reduce composition freedom
    """
    return li

def getLayerNames(path):
    """
    Get the name of each layer in the image
        first check the id attribute of <svg>
        then check the id attribute of <g>s
    """
    doc = parse(path)
    svg_list = doc.getElementsByTagName('svg')
    assert(len(svg_list) == 1)
    svg = svg_list[0]
    # use * instead of g, some layer may not be a group
    layers = [g for g in doc.getElementsByTagName('*') \
              if g.nodeType == 1 and \
                 g.hasAttribute('id') and \
                 g.getAttribute('id').startswith('_x23_')]

    if layers:
        return rectifyLayer(path, [cleanName(l.getAttribute('id')) for l in layers])
    else:
        if svg.hasAttribute('id') and \
           svg.getAttribute('id').startswith('_x23_'):
            # if single layer case, id should belong to <svg>
            return [cleanName(svg.getAttribute('id'))]
        else:
            raise ValueError('No valid id name found!')

def checkLayerName(name):
    obj = '\[\w+(,\w+)*\]'
    act_obj = '\w+(%s)*' % obj
    reg_single = '\w+(\(%s(,%s)*\))+' % (act_obj, act_obj)
    reg_multi = 'group\(have\[%s(,%s)*\]\)' % (reg_single,
                                               reg_single)

    from rules.labels import subjects

    if name.startswith('#background'):
        if not name == '#background':
            raise KeyError(name)
    elif name.startswith('#group'):
        if not re.match(r'^#%s$' % reg_multi, name):
            raise KeyError(name)
    elif name.startswith('#accessory'):
        if not re.match(r'#accessory(\(%s(,%s)*\))*' % (act_obj, act_obj), name):
            raise KeyError(name)
    elif any([name.startswith('#%s' % key) for categ in subjects for key in subjects[categ]]):
        if not re.match(r'^#%s$' % reg_single, name):
            raise KeyError(name)
    else:
        raise KeyError(name)

class LayerName:
    """
    given layer Name, return nested entities list
    E.g. subj(act[obj]) -> {'subj': {'act': ['obj']}}
    """
    def __init__(self, s=''):
        assert(isinstance(s, str))
        if s: checkLayerName(s)

        self.s = s
#         self.obj_ptn = '\[\w+(?=,\w+)*\]'
#         self.act_obj_ptn = '\w+(?=%s)?' % self.obj_ptn

        self.nested_entities_ = self._get_nested_entities()
        self.entities_ = self._get_entities()
        self.triples_ = self._get_triples()

    def __eq__(self, other):
        """
        nested entities are same or triples are same
        """
        return self.nested_entities_ == other.nested_entities_

    def __hash__(self):
        return hash(self.triples_)

    def __repr__(self):
        return self.s

    def _get_subjs(self):
        """
        define a exclusion variable to determine if resolve conflict
            same variable used by get_nested_subjs
        """
        if self.s.startswith('#background'):
            return ['background']
        if self.s.startswith('#accessory'):
            return ['accessory']
        if self.s.startswith('#group'):
            # action can not be neglected, thus here we can append \(
            # but if actions can be neglected, need to modify here
            subjs = re.findall('[\[|,](\w+)\(', self.s)
            if len(subjs) != len(set(subjs)):
                # there are multiple subjects are duplicate, e.g. man(), man()
                # name them sequencially
                duplicates = list(set([subj for subj in subjs if subjs.count(subj)>1]))
                for subj in duplicates:
                    for i in range(subjs.count(subj)):
                        self.s = re.sub('(?<=[\[,])%s(?=\()' % subj,
                                        '%s%i' % (subj, i+1),
                                        self.s, count=1)
                # find the subjects again
                subjs = re.findall('[\[|,](\w+)\(', self.s)
        else:
            subjs = re.findall('^#(\w+)\(', self.s)
            assert len(subjs) == 1, (self.s, subjs)
        # make sure there are no duplicated subjects
        assert(len(subjs) == len(set(subjs)))
        return subjs

    def _get_acts(self):
        """
        given subj, find associated actions
            what if subjs are same? E.g. there are two man in the same layer!!
        """
        subjs = self._get_subjs()
        # if group, remove group mark
        if self.s.startswith('#group'):
            s = re.sub('#group\(have', '', self.s)
            s = s.rstrip(')')
        else:
            # make the form consistent
            s = '[%s]' % self.s.lstrip('#')

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
                    # acts[subj].extend(act.split(','))
                    acts[subj] |= set(act.split(','))
                else:
                    # acts[subj].append(act)
                    acts[subj].add(act)

        return acts

    def _get_nested_entities(self):
        """
        given subj, actions,  find associated objects
        """
        if not self.s:
            return defaultdict(lambda: defaultdict(set))
            # return defaultdict(lambda: defaultdict(list))
            # defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        acts = self._get_acts()

        # if group, remove group mark
        if self.s.startswith('#group'):
            s = re.sub('#group\(have', '', self.s)
            s = s.rstrip(')')
        else:
            s = '[%s]' % self.s.lstrip('#')

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
                            objs[subj][act] |= set(obj.split(','))
                        else:
                            # objs[subj][act].append(obj)
                            objs[subj][act].add(obj)

        return objs

    def _get_entities(self):
        """
        a dictionary of all the entities list
            todo: need to resolve multiple subjects, because get_subjs resolve conflicts
        """
        entities = defaultdict(lambda: defaultdict(int))
        for subj in self.nested_entities_:
            # to-do
            sub = subj # re.sub(r'\d*$','',subj)
            entities['subj'][sub] += 1 #.add(subj)
            for act in self.nested_entities_[subj]:
                # same actions in different subject will be counted separately
                entities['act'][act] += 1 #.add(act)
                for obj in self.nested_entities_[subj][act]:
                    entities['obj'][obj] += 1 #.add(obj)
        return entities

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

    def absorb(self, other, subj_exclusion=False):

        # merge nested entites
        if not subj_exclusion:

            # merge man1 and man2
            self.collapse_subj()
            other.collapse_subj()
            absorbNestedDict(self.nested_entities_,
                               other.nested_entities_)

        else:
            """
            now are using dict of dict of set, may should do some modification here
            """
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

        # merge entities
        # show new entities list
        # self.entities_ = self.__get_entities()
        for type_ in other.entities_:
            for entity in other.entities_[type_]:
                self.entities_[type_][entity] += other.entities_[type_][entity]

    def collapse_subj(self):
        """
        collapse subjk such that we no longer label two men in one layer separately
        """
        # collapse nested dict
        # nested_entities_clps_ = defaultdict(lambda: defaultdict(list))
        nested_entities_clps_ = defaultdict(lambda: defaultdict(set))
        for subj in self.nested_entities_:
            if re.match(r'^\w+\d+$', subj):
                sub = re.sub(r'\d*$', '', subj)
                absorbNestedDict(nested_entities_clps_[sub],
                                 self.nested_entities_[subj])
            else:
                nested_entities_clps_[subj] = self.nested_entities_[subj]
        self.nested_entities_ = nested_entities_clps_

        # collapse dict, such that count are summed
        entities_clps_ = defaultdict(lambda: defaultdict(int))
        for type_ in self.entities_:
            for entity in self.entities_[type_]:
                if re.match(r'^\w+\d+$', entity):
                    sub = re.sub(r'\d*$', '', entity)
                    entities_clps_[type_][sub] += self.entities_[type_][entity]
                else:
                    entities_clps_[type_][entity] = self.entities_[type_][entity]
        self.entities_ = entities_clps_


#     def collapse_act(self):

    def ravel(self):
        """
            ravel a layer to a tuple of keywords (weighted)
                what to do with keyword occurring more than once
        """
        pass
        return tuple()

    def print_(self):
        for subj in self.nested_entities_:
            if not self.nested_entities_[subj]:
                print('%s(subj)' % subj)
            for act in self.nested_entities_[subj]:
                if not self.nested_entities_[subj][act]:
                    print('%s(subj) - %s(act)' % (subj, act))
                for obj in self.nested_entities_[subj][act]:
                    print('%s(subj) - %s(act) - %s(obj)' % (subj, act, obj))

    def plot(self, save_fig=False):

        # regain entities, because merge entities are sets
        entities_ = self._get_entities()

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
            return [ atoi(c) for c in re.split(r'(\d+)', text) ]

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
                if act != 'have':
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

