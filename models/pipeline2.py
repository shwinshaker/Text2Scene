#!./env python

# from rules.labels import subjects
import spacy
nlp = spacy.load("en_core_web_sm")
from collections import defaultdict
from tools.common import ddict2dict, enableQuery, enableQuery_, getElementFromSet
from tools.instance import Node, CombToken
from tools.knowledge import LayerBase
from tools.containers import Picture, LayerName
from query_relatedness import query_simi
from .metric import WeightedMeanIOU
import warnings

@enableQuery_
class Ground:
    def __init__(self, img_dir='images'):
        # self.dict_dir = dict_dir
        self.layerbase = LayerBase(img_dir=img_dir)
        self.collocations_ = self.layerbase.collocations_
        self.entities_ = self.layerbase.entities_
        self.have = Node('have', 'act')

    def __call__(self, filename=None, text=None):

        if not text:
            assert(filename)
            with open(filename) as f:
                text = f.read()
        # print(text.strip('\n'))
        doc = nlp(u'%s' % text.strip('\n'))

        nested = defaultdict(lambda: defaultdict(set))
        tokens = self.get_tokens(doc)
        # print(tokens)

        self.ground_subj(tokens, nested)

        self.ground_act(tokens, nested)
        if not all([t.pos_ != 'VERB' for t in tokens]):
            warnings.warn('Verbs not exhausted!')
            print([t for t in tokens if t.pos_ == 'VERB'])

        self.ground_obj(tokens, nested)
        if tokens:
            warnings.warn('Tokens not exhausted!')
            print('-> left ungrounded tokens:', tokens)

        self.dup_combine(nested)

        self.conj_copy(nested)

        layers = self.slice_into_layers(nested)

        return layers

    def get_tokens(self, doc):
        return [t for t in doc if not t.is_stop and not t.is_punct]

    def ground_subj(self, tokens_, nested_):

        ## query the base to identify a subject
        tokens_copy = tokens_.copy()
        subjs = [subj for subj in self.collocations_]
        for token in tokens_copy:
            if token.pos_ == 'NOUN':
                tup = self.get_simi_keyword(token, subjs, thresh=0.5)
                if tup:
                    subj_, _ = tup
                    tokens_.remove(token)
                    nested_[CombToken(token, subj_)] = defaultdict(set)

    def get_simi_keyword(self, token, keywords, thresh=0.5):
        tups = [(k, self.query_simi(token.lemma_, k.t)) for k in keywords]
        simi_key, simi_ = sorted(tups,
                                 key=lambda x: (x[1], x[0].count))[-1]
        if simi_ >= thresh:
            return simi_key, simi_
        return None

    def bind_keyword(self, token, attr='obj',
                     subj=None, act=None, thresh=0.2):
        if attr == 'act':
            if subj:
                keywords = [k for k in self.collocations_[subj]]
            else:
                keywords = [k for k in self.entities_['act']]
        elif attr == 'obj':
            if subj and act:
                keywords = [k for k in self.collocations_[subj][act]]
            elif subj:
                keywords = [k for a in self.collocations_[subj] for k in self.collocations_[subj][a]]
            else:
                keywords = [k for k in self.entities_['obj']]
        else:
            raise KeyError

        tup = self.get_simi_keyword(token, keywords, thresh=thresh)
        if tup:
            k_, _ = tup
        else:
            k_ = None # Node('', attr=attr)
        return CombToken(token, k_)

    def wrap_multiple_actions(self, token, subj, acts, thresh=0.2):
        tups = []
        for act in acts:
            if not self.collocations_[subj][act]: continue
            tup = self.get_simi_keyword(token,
                                   self.collocations_[subj][act],
                                   thresh=thresh)
            if tup:
                tups.append((act,) + tup)
        if tups:
            return sorted(tups, key=lambda x: (x[-1], x[0].count))[-1]
        return None

    def find_most_simi_subj(self, subjs, token,
                            attr='obj', fix_have=True):
        assert(isinstance(token, spacy.tokens.token.Token))
        assert(all([isinstance(subj, Node) for subj in subjs]))

        if attr == 'obj':
            most_simi_ = []
            for subj in subjs:
                if fix_have:
                    assert(all([self.have in self.collocations_[s] for s in subjs]))
                    if not self.collocations_[subj][self.have]:
                        continue
                    tup = self.get_simi_keyword(token,
                                           self.collocations_[subj][self.have],
                                       thresh=0.2)
                else:
                    if not self.collocations_[subj]: continue
                    tup = self.wrap_multiple_actions(token, subj,
                                        self.collocations_[subj],
                                        thresh=0.2)
                if tup:
                    most_simi_.append((subj,) + tup)

            if most_simi_:
                if fix_have:
                    sort_f = lambda x: (x[-1], getElementFromSet(self.collocations_[x[0]][self.have], x[1]).count)
                else:
                    sort_f = lambda x: (x[-1], getElementFromSet(self.collocations_[x[0]][x[1]], x[2]).count)
                return sorted(most_simi_, key=sort_f)[-1]

        elif attr == 'act':
            most_simi_ = []
            for subj in subjs:
                # if no action under this suject, skip it
                if not self.collocations_[subj]: continue
                tup = self.get_simi_keyword(token,
                                       self.collocations_[subj],
                                       thresh=0.2)
                if tup:
                    most_simi_.append((subj,) + tup)
            if most_simi_:
                sort_f = lambda x: (x[-1], getElementFromSet(self.collocations_[x[0]], x[1]).count)
                return sorted(most_simi_, key=sort_f)[-1]
        else:
            raise KeyError

        return None

    def ground_act(self, tokens_, nested_):

        ## ---- syntactical parency
        tokens_copy = tokens_.copy()
        for token in tokens_copy:
            for key in nested_:
                if token == key.token.head and key.token.dep_ == 'nsubj':
                    tokens_.remove(token)
                    nested_[key][self.bind_keyword(token, attr='act', subj=None)] = set()

        ## ---- conjuncted verbs
        tokens_copy = tokens_.copy()
        saved_tups = []
        for token in tokens_copy:
            for subj in nested_:
                for act in nested_[subj]:
                    if token.head == act.token and token.pos_ == 'VERB':
                        assert(token.dep_ in ['conj', 'xcomp', 'advcl']), token.dep_
                        tokens_.remove(token)
                        saved_tups.append((subj, token))
        for subj, token in saved_tups:
            nested_[subj][self.bind_keyword(token, subj=None, attr='act')] = set()

        ## ---- common root verbs
        ### if the verb has the common root with any of the subjects, bind it. This cause confusion when a sentence contains two or more subjects
        tokens_copy = tokens_.copy()
        saved_tups = []
        for token in tokens_copy:
            if token.pos_ == 'VERB':
                for subj in nested_:
                    if token.sent.root == subj.token.sent.root:
                        tokens_.remove(token)
                        saved_tups.append((subj, token))
                        break
        for subj, token in saved_tups:
            nested_[subj][self.bind_keyword(token, subj=None, attr='act')] = set()

        ### finally if still some verbs left, use knowledge base
        ## subject-object collocation knowledge ground, subjects in the layerbase
        tokens_copy = tokens_.copy()
        saved_tups = []
        subjs = [subj for subj in self.collocations_]
        for token in tokens_copy:
            if token.pos_ == 'VERB':
                tup = self.find_most_simi_subj(subjs, token, attr='act')
                if tup:
                    subj_, act_, s_ = tup
                    tokens_.remove(token)
                    saved_tups.append((subj_, act_, token))
        for subj, act, token in saved_tups:
            nested_[CombToken(None, subj)][CombToken(token, act)] = set()


    def ground_obj(self, tokens_, nested_):

        ## syntactically ground
        tokens_copy = tokens_.copy()
        saved_tups = []
        for token in tokens_copy:
            for subj in nested_:
                for act in nested_[subj]:
                    if token.head == act.token and token.pos_ == 'NOUN':
                        if token.dep_ in ['dobj']:
                            mapped = self.bind_keyword(token,
                                                  attr='obj',
                                                  subj=subj.keyword)
                            if mapped.keyword:
                                tokens_.remove(token)
                                saved_tups.append((subj, act,
                                                   token, mapped))
        for subj, act, token, mapped in saved_tups:
            nested_[subj][act].add(mapped)

        # ground to current surrounding subjects based on knowledge
        srd_subjects = [(subj.keyword, subj) for subj in nested_]
        if srd_subjects:
            subjs, mapped = zip(*srd_subjects)
            tokens_copy = tokens_.copy()
            saved_tups = []

            fix_have=False
            for token in tokens_copy:
                tup = self.find_most_simi_subj(subjs, token,
                                              fix_have=fix_have)
                if tup:
                    tokens_.remove(token)
                    if fix_have:
                        subj_, obj_, s_ = tup
                        saved_tups.append((mapped[subjs.index(subj_)], obj_, token))
                    else:
                        subj_, act_, obj_, s_ = tup
                        saved_tups.append((mapped[subjs.index(subj_)], act_, obj_, token))
            if fix_have:
                for subj, obj, token in saved_tups:
                    if CombToken(None, self.have) not in nested_[subj]:
                        nested_[subj][CombToken(None, self.have)] = set()
                    nested_[subj][CombToken(None, self.have)].add(CombToken(token, obj))
            else:
                for subj, act, obj, token in saved_tups:
                    if CombToken(None, act) not in nested_[subj]:
                        nested_[subj][CombToken(None, act)] = set()
                    nested_[subj][CombToken(None, act)].add(CombToken(token, obj))

    #     ## other objects, just query the surroundings in knowledge and see which it belongs to
        tokens_copy = tokens_.copy()
        saved_tups = []
        subjs = [subj for subj in self.collocations_ if self.have in self.collocations_[subj]]
        for token in tokens_copy:
            tup = self.find_most_simi_subj(subjs, token)
            if tup:
                subj_, obj_, s_ = tup
                tokens_.remove(token)
                saved_tups.append((subj_, obj_, token))
        for subj, obj, token in saved_tups:
            if CombToken(None, self.have) not in nested_[CombToken(None, subj)]:
                nested_[CombToken(None, subj)][CombToken(None, self.have)] = set()
            nested_[CombToken(None, subj)][CombToken(None, self.have)].add(CombToken(token, obj))

    def conj_copy(self, nested_):
        """
        Error: temporarily ignored
        conjunction copy should be done only after syntactical parse!
            otherwise cause unexpected tree
            E.g. "A man is sitting on a printer looking at his phone. A man and a woman are bending over to file."
                 "woman" is attached with "phone". Cause problem when conjunctedly copy man's verbs and objects
        """
        # subjs = []
        saved_tups = []
        for subj in nested_:
            if subj.token:
                if subj.token.dep_ == 'conj':
                    # assert(not nested_[subj]), nested_[subj]
                    for subj_ in nested_:
                        if subj.token.head == subj_.token and nested_[subj_]:
                            saved_tups.append((subj, subj_))
                            break

        for subj, subj_ in saved_tups:
            nested_[subj] = nested_[subj_]

    def dup_combine(self, nested_):
        saved_tups = []
        for subj in nested_:
            assert(subj.keyword)
            act_keys = [a.keyword for a in nested_[subj]]
            if len(act_keys) == len(set(act_keys)):
                continue
            dup_keys = [a for a in nested_[subj] if act_keys.count(a.keyword) > 1]
            for k in dup_keys:
                # only combine those with token not specified
                if k.token is None:
                    k_dup = [k_ for k_ in dup_keys if k_.keyword == k.keyword and k_.token][0]
                    dup_keys.remove(k)
                    saved_tups.append((subj, k_dup, k))
        for subj, k_des, k in saved_tups:
            nested_[subj][k_des] |= nested_[subj][k]
            del nested_[subj][k]

    def slice_into_layers(self, nested_):

        if not nested_: return []

        from rules.labels import subjects
        # solidify first
        nested_ = ddict2dict(nested_)

        subjs = list(nested_)
        group_list = [[subjs[0]]]
        subjs = subjs[1:]
        while subjs:
            for subj in subjs:
                # for group in group_list:
                matched = [g for g in group_list if subj.token and g[0].token and g[0].token.sent.root==subj.token.sent.root and subj.keyword.t in subjects['character']]
                if matched:
                    assert(len(matched) == 1)
                    matched[0].append(subj)
                    subjs.remove(subj)
                else:
                    group_list.append([subj])
                    subjs.remove(subj)

        layers = []
        for group in group_list:
            layer = {}
            for subj in group:
                layer[subj] = nested_[subj]
            layers.append(layer)
        return tuple(layers)


class Translate:

    # @staticmethod
    # def from_file():
    # return Translate()

    def __init__(self, img_dir='images', dict_dir='.'):
        self.ground = Ground(img_dir=img_dir, dict_dir=dict_dir)
        # self.ground = Ground(img_dir=img_dir)
        # self.layerbase = LayerBase()
        # self.metric = WeightedMeanIOU(dict_dir=dict_dir)
        self.metric = WeightedMeanIOU(dict_dir=dict_dir)

        # wrap function
        def __simi(*args, **kwargs):
            s = self.metric.layer_simi(*args, **kwargs)
            return s['overall']
        self.simi = __simi

    def __call__(self, text=None, path=None, verbose=True):
        if text is None:
            assert(path)
            layers = self.ground(path)
        else:
            layers = self.ground(text=text)
        if not layers: return []
        matched_layers, simi = self.translate(layers)
        if verbose:
            print('layer graph: ', layers)
            print('matched layers: ', matched_layers)
            print('mean layer similarity: %.4f' % (sum(simi)/len(simi)))
        return Picture.from_layers(self.sort(matched_layers))
        # return ['material/%s.png' % l.s for l in self.sort(matched_layers)]

    def translate(self, layers):
        # layers_ravel = [self.ravel_layer(layer) for layer in layers]
        most_simi_layers = []
        for layer in layers: #layers_ravel:
            tups = []
            for layer_ in self.ground.layerbase.layer_vocab_:
                # tups.append((layer_, WeightedMeanIOU.layer_simi(layer,
                #                                      self.ravel_layer(layer_.nested_entities_))))
                tups.append((layer_, self.simi(layer, layer_.nested_entities_)))
            most_simi_layers.append(sorted(tups, key=lambda x: x[1])[-1])
        simi_layers, simi = zip(*most_simi_layers)
        return simi_layers, simi

    def sort(self, layers):
        """
        sort layers based on specific order
        """
        from rules.labels import subjects
        dic = {'background': 0,
               'surrounding': 1,
               'character': 2,
               'accessory': 3}
        def to_category(subj):
            if subj in subjects['character']:
                return 'character'
            elif subj in subjects['surrounding']:
                return 'surrounding'
            else:
                return subj

        return tuple(sorted(layers, key=lambda l: dic[to_category(list(l.entities_['subj'])[0].t)]))
