#!./env python

from nltk import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords

import spacy # use spacy now for sophicated tagging
from spacy.lemmatizer import Lemmatizer
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES

import string
import warnings

from tools.instance import Node

class SimpleLemmaTokenizer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe(self.__filter, last=True)
        self.nlp.add_pipe(self.__to_node, last=True)

    def __filter(self, doc):
        return [t for t in doc if not t.is_stop and not t.is_punct]
        # return [t for t in doc if not t.is_stop]

    def __to_node(self, doc):
        return [Node(t.lemma_, t.pos_) for t in doc]

    def __call__(self, sentence):
        return self.nlp(sentence.strip('\n'))


class SpacyLemmaTokenizer:

    """
    rewrite this... spacy is too damned simple
    """
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.lemmatizer = Lemmatizer(LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES)

    def penn_to_lemma(self, tag):
        """
        Convert output of pos tagger to wordnet tags
        Only nouns, verbs, adjectives and adverbs will be kept.
        """
        if tag.startswith('J'):
            return 'ADJ'
        elif tag.startswith('N'):
            return 'NOUN'
        elif tag.startswith('R'):
            return 'ADV'
        elif tag.startswith('V'):
            return 'VERB'
        return None

    def le_to_wn(self, tag):
        return tag
        dic = {'ADJ': wn.ADJ,
               'NOUN': wn.NOUN,
               'ADV': wn.ADV,
               'VERB': wn.VERB}
        return dic[tag]

    def lemmatize(self, token, tag):
        lemma_tag = self.penn_to_lemma(tag)
        if lemma_tag is None: return Node(token, tag) #Node(token, 'UNK')
        return Node(self.lemmatizer(token, lemma_tag)[0], self.le_to_wn(lemma_tag))

    def __filter(self, token):
        return token.is_stop or token.is_punct

    def __call__(self, sentence):
        doc = self.nlp(sentence.strip('\n'))
        return [self.lemmatize(token.text, token.tag_) for token in doc if not self.__filter(token)]


### text processing
class LemmaTokenizer(object):
    def __init__(self):
        self.tokenize = word_tokenize
        self.pos_tagger = pos_tag
        self.lemma = WordNetLemmatizer()
        # later
        # self.corrector = lambda x: x.lower() # SpellCorrector()
        # todo
        # to deal with abbreviations better, like it's can't

        self.stopwords = stopwords.words('english')
        self.punctuation = string.punctuation


    def corrector(self, token):
        # todo
        return token.lower()

    def penn_to_wn(self, tag):
        """
        Convert output of pos tagger to wordnet tags
        Only nouns, verbs, adjectives and adverbs will be kept.
        """
        if tag.startswith('J'):
            return wn.ADJ
        elif tag.startswith('N'):
            return wn.NOUN
        elif tag.startswith('R'):
            return wn.ADV
        elif tag.startswith('V'):
            return wn.VERB
        return None

    def synsetting(self, lemma, tag=None):
        # synset only disambiguate POS. Eg. noun and verb
        synsets = wn.synsets(lemma, tag)
        if len(synsets) >= 1:
            return synsets[0].name()
        warnings.warn('%s with tag %s does not belong to any synsets.' % (lemma, tag))
        return None

    def wsd(self, sent, sentence):
        # word sense disambiguation is unstable
        return [lesk(self.tokenize(sentence), lemma) for lemma in sent]

    def lemmatize(self, token, tag):
        token = self.corrector(token)
        tag = self.penn_to_wn(tag)

        # if nouns, verbs, adjs, advs, lemmatize
        if tag: # N,V,ADJ,ADV
            lemma = self.lemma.lemmatize(token, tag)
            # remove stopwords
            # Eg. remove 'be'
            if lemma in self.stopwords:
                return None
            ### wn.morphy can also do this job
            ### actually lemmatize calls morphy
            ### rule-based suffix detachment. Eg. corpora -> corpus
            # lemma = wn.morphy(self.corrector(token), tag)
            return Node(lemma, tag)
            # return self.synsetting(lemma, tag)

        # remove stopwords
        if token in self.stopwords:
            return None

        # remove punctuation
        if token in self.punctuation:
            return None

        return Node(token, 'UNK') #self.synsetting(token)

    def __filter(self, tokens):
        return [t for t in tokens if t]

    def __call__(self, sentence):
        # print(word_tokenize(sentence))
        # print(pos_tag(word_tokenize(sentence)))
        return self.__filter([self.lemmatize(t, tag) for t, tag in self.pos_tagger(self.tokenize(sentence))])
        #
        # return self.wsd(self.__filter([self.lemmatize(t, tag) for t, tag in pos_tag(word_tokenize(sentence))]), sentence)

# from rules.labels import subjects
# import spacy
# nlp = spacy.load("en_core_web_sm")
# from collections import defaultdict
# from tools.common import ddict2dict
# from tools.instance import Node
# from tools.knowledge import LayerBase
# from query_relatedness import query_simi
# import warnings

class Ground:
    def __init__(self):
        self.layerbase = LayerBase()
        self.have = Node('have', 'act')
        # self.

#     def incre_name(s, dic):
#         count = 0
#         for k in dic:
#             # remove any tail digits
#             sub = re.sub(r'(?<=\w)\d+$','', k)
#             if re.match(r'%s\d*' % sub, s):
#                 # print(count, r'%s\d*' % sub, s)
#                 count += 1
#         if count > 0:
#             return '%s%i' % (s, count)
#         return s

def get_tokens(doc):
    return [t for t in doc if not t.is_stop and not t.is_punct]

def get_simi_keyword(token, keywords, thresh=0.5):

    tups = [(k, query_simi(token.lemma_, k.t)) for k in keywords]
    simi_key, simi_ = sorted(tups, key=lambda x: (x[1], x[0].count))[-1]
    if simi_ >= thresh:
        return simi_key, simi_
#     return None
#     for keyword in keywords:
#         if  > thresh:
#             return keyword
    return None

class MappedToken:
    def __init__(self, token, keyword):
        if token:
            assert(isinstance(token, spacy.tokens.token.Token))
        if keyword:
            assert(isinstance(keyword, Node))
        self.token = token
        self.keyword = keyword

        self.tup = (self.token, self.keyword)

    def __repr__(self):
        if self.token is None:
            return '->%s' % (self.keyword.t)
        if self.keyword is None:
            return '%s->' % (self.token.lemma_)
        return '%s->%s' % (self.token.lemma_, self.keyword.t)

    def __eq__(self, other):
        return self.tup == other.tup

    def __hash__(self):
        return hash(self.tup)

def ground_subj(tokens_, nested_):

    ## query the base to identify a subject
    tokens_copy = tokens_.copy()
    subjs = [subj for subj in layerbase.collocations_]
    for token in tokens_copy:
        if token.pos_ == 'NOUN':
            tup = get_simi_keyword(token, subjs, thresh=0.5)
            if tup:
                subj_, _ = tup
                tokens_.remove(token)
                nested_[MappedToken(token, subj_)] = defaultdict(set)
#         for type_ in subjects:
#             if token.lemma_ in subjects[type_]:
#                 tokens_.remove(token)
#                 nested_[token] = defaultdict(set)
#                 if token.lemma_ not in nested_:
#                     map_dict[token] = token.lemma_
#                     nested_[token.lemma_] = defaultdict(set)
#                 else:
#                     lemma_i = incre_name(token.lemma_, nested_)
#                     map_dict[token] = lemma_i
#                     nested_[lemma_i] = defaultdict(set)

def bind_keyword(token, dest='obj', subj=None, act=None, thresh=0.3):
    # bind keyword
    # if act is None:
    if dest == 'act':
        # used to bind actions
        if subj:
            keywords = [k for k in layerbase.collocations_[subj]]
        else:
            keywords = [k for k in layerbase.entities_['act']]
        attr = 'act'
    elif dest == 'obj':
        # used to bind objects
        # maybe, search all objects regardless of subj and act
        # error case: "woman transfer money" should be woman transfer and "money"
        if subj and act:
            keywords = [k for k in layerbase.collocations_[subj][act]]
        elif subj:
            keywords = [k for a in layerbase.collocations_[subj] for k in layerbase.collocations_[subj][a]]
        else:
            keywords = [k for k in layerbase.entities_['obj']]
        attr = 'obj'
    else:
        raise KeyError

    tup = get_simi_keyword(token, keywords, thresh=thresh)
    if tup:
        k_, _ = tup
    else:
        k_ = None # Node('', attr=attr)
    return MappedToken(token, k_)

def wrap_multiple_actions(token, subj, acts, thresh=0.2):
    tups = []
    for act in acts:
        if not layerbase.collocations_[subj][act]: continue
        tup = get_simi_keyword(token,
                               layerbase.collocations_[subj][act],
                               thresh=thresh)
        if tup:
            tups.append((act,) + tup)
    if tups:
        return sorted(tups, key=lambda x: (x[-1], x[0].count))[-1]
    return None

def find_most_simi_subj(subjs, token, dest='obj', fix_have=True):
    assert(isinstance(token, spacy.tokens.token.Token))
    assert(all([isinstance(subj, Node) for subj in subjs]))
    # assert(all([s.t in subjects['surrounding'] for s in subjs]))
    # search all subjects, not just surrounding subjects. E.g. Alien have robot
    if dest == 'obj':
        most_simi_ = []
        for subj in subjs:
            if fix_have:
                assert(all([Node('have', attr='act') in layerbase.collocations_[s] for s in subjs]))
                if not layerbase.collocations_[subj][Node('have', attr='act')]:
                    continue
                tup = get_simi_keyword(token,
                                       layerbase.collocations_[subj][Node('have', attr='act')],
                                   thresh=0.2)
            else:
                if not layerbase.collocations_[subj]: continue
                tup = wrap_multiple_actions(token, subj,
                                    layerbase.collocations_[subj],
                                    thresh=0.2)
            if tup:
                most_simi_.append((subj,) + tup)

        if most_simi_:
            if fix_have:
                sort_f = lambda x: (x[-1], get_element_from_set(layerbase.collocations_[x[0]][Node('have', attr='act')], x[1]).count)
            else:
                sort_f = lambda x: (x[-1], get_element_from_set(layerbase.collocations_[x[0]][x[1]], x[2]).count)
            return sorted(most_simi_, key=sort_f)[-1]

    elif dest == 'act':
        most_simi_ = []
        for subj in subjs:
            # if no action under this suject, skip it
            if not layerbase.collocations_[subj]: continue
            tup = get_simi_keyword(token,
                                   layerbase.collocations_[subj],
                                   thresh=0.2)
            if tup:
                most_simi_.append((subj,) + tup)
        if most_simi_:
            sort_f = lambda x: (x[-1], get_element_from_set(layerbase.collocations_[x[0]], x[1]).count)
            return sorted(most_simi_, key=sort_f)[-1]
    else:
        raise KeyError

    return None

def ground_act(tokens_, nested_):

    ## ---- syntactical parency
    tokens_copy = tokens_.copy()
    for token in tokens_copy:
        for key in nested_:
            if token == key.token.head and key.token.dep_ == 'nsubj':
                tokens_.remove(token)

                # bind keyword
#                 acts = [a for a in layerbase.collocations_[key.keyword]]
#                 tup = get_simi_keyword(token, acts, thresh=0.3)
#                 if tup:
#                     act_, _ = tup
#                 else:
#                     act_ = Node('', attr='act')
                # print(token, key.keyword)
                nested_[key][bind_keyword(token, dest='act', subj=None)] = set()

    ## ---- conjuncted verbs
    tokens_copy = tokens_.copy()
    # cannot pickle a spacy.token
    ## nested_copy = deepcopy(nested_)
    # cannnot modify a dict during iteration, thus save keys
    saved_tups = []
    for token in tokens_copy:
        for subj in nested_:
            for act in nested_[subj]:
                if token.head == act.token and token.pos_ == 'VERB':
                    assert(token.dep_ in ['conj', 'xcomp', 'advcl']), token.dep_
                    tokens_.remove(token)
                    saved_tups.append((subj, token))
    for subj, token in saved_tups:
        nested_[subj][bind_keyword(token, subj=None, dest='act')] = set()

    ## ---- other verbs
    ### if the verb has the common root with any of the subjects, bind it. This cause confusion when a sentence contains two or more subjects
    tokens_copy = tokens_.copy()
    saved_tups = []
    for token in tokens_copy:
        if token.pos_ == 'VERB':
            for subj in nested_:
                if token.sent.root == subj.sent.root:
                    tokens_.remove(token)
                    saved_tups.append(subj, token)
    for subj, token in saved_tups:
        nested_[subj][bind_keyword(token, subj=None, dest='act')] = set()

    ### finally if still some verbs left, use knowledge base
    ## subject-object collocation knowledge ground, subjects in the layerbase
    tokens_copy = tokens_.copy()
    saved_tups = []
    subjs = [subj for subj in layerbase.collocations_]
    for token in tokens_copy:
        if token.pos_ == 'VERB':
            tup = find_most_simi_subj(subjs, token, dest='act')
            if tup:
                subj_, act_, s_ = tup
                tokens_.remove(token)
                saved_tups.append((subj_, act_, token))
    for subj, act, token in saved_tups:
        nested_[MappedToken(None, subj)][MappedToken(token, act)] = set()

# static var stuff
# related dict needs to transformed to dict
# def query_related(t, k):
#     import dill
#     with open('relateDict.pkl', 'rb') as f:
#         relateDict = dill.load(f)
#     if k in relateDict and t in relateDict[k]:
#         return relateDict[k][t]

#     import requests
#     return requests.get('http://api.conceptnet.io/relatedness?node1=/c/en/%s&node2=/c/en/%s' % (k, t)).json()['value']

def get_element_from_set(set_, e_):
    for e in set_:
        if e == e_:
            return e



def ground_obj(tokens_, nested_):

    ## syntactically ground
    ### E.g. man plays computer: computer -> play -> man
    tokens_copy = tokens_.copy()
    saved_tups = []
    for token in tokens_copy:
        for subj in nested_:
            for act in nested_[subj]:
                if token.head == act.token and token.pos_ == 'NOUN':
                    if token.dep_ in ['dobj']:
                        # unbound subjects are neglected, such as "couple"
                        mapped = bind_keyword(token,
                                              dest='obj',
                                              subj=subj.keyword)
                        # print(token, keyword)
                        if mapped.keyword:
                            tokens_.remove(token)
                            saved_tups.append((subj, act,
                                               token, mapped))
    for subj, act, token, mapped in saved_tups:
        # nested_[subj][act].add(token)
        nested_[subj][act].add(mapped)

    # ground to current surrounding subjects based on knowledge
    ## subject-object collocation knowledge ground, current subjects only
    ### surrounding only. because obj in character must be syntactically grounded
    ### not necessarily, obj can be knowledgely grounded to characters if th action is have. E.g. Alien have robot

    ## srd_subjects = [(subj.keyword, subj) for subj in nested_ if subj.keyword.t in subjects['surrounding']]
    # srd_subjects = [(subj.keyword, subj) for subj in nested_ if Node('have', attr='act') in layerbase.collocations_[subj.keyword]]
    srd_subjects = [(subj.keyword, subj) for subj in nested_]
    ## if no surrounding subjects are captured now, skip this step
    if srd_subjects:
        subjs, mapped = zip(*srd_subjects)
        tokens_copy = tokens_.copy()
        saved_tups = []

        fix_have=False
        for token in tokens_copy:
            tup = find_most_simi_subj(subjs, token,
                                      fix_have=fix_have)
            if tup:
                tokens_.remove(token)
                if fix_have:
                    subj_, obj_, s_ = tup
                    saved_tups.append((mapped[subjs.index(subj_)], obj_, token))
                else:
                    subj_, act_, obj_, s_ = tup
                    print(obj_)
                    saved_tups.append((mapped[subjs.index(subj_)], act_, obj_, token))
                ## use original text in the description as key
                ## or use grounding keyword as key
        if fix_have:
            for subj, obj, token in saved_tups:
                if MappedToken(None, Node('have', attr='act')) not in nested_[subj]:
                    nested_[subj][MappedToken(None, Node('have', attr='act'))] = set()
                nested_[subj][MappedToken(None, Node('have', attr='act'))].add(MappedToken(token, obj))
        else:
            for subj, act, obj, token in saved_tups:
                if MappedToken(None, act) not in nested_[subj]:
                    nested_[subj][MappedToken(None, act)] = set()
                nested_[subj][MappedToken(None, act)].add(MappedToken(token, obj))

#         for subj in nested_:
#             if subj.lemma_ in subjects['surrounding']:
#                 assert(subj.lemma_ in layerbase.layer_merge_.nested_entities_)
# #                 if token.lemma_ in layerbase.layer_merge_.nested_entities_[subj.lemma_]['have']:
# #                     print(subj, token)
#                 # get the most similar obj in the vocabulary under this subject
#                 obj_ = get_simi_obj(token.lemma_,
#                                     layerbase.layer_merge_.nested_entities_[subj.lemma_]['have'],
#                                     thresh=0.2)
#                 print(token.lemma_, obj_)
#                 if obj_:
#                     tokens_.remove(token)
#                     saved_tups.append((subj, token))
#                     # prevent other subjs containing the same object emerging
#                     # first come, first serve
#                     break
#     for subj, token in saved_tups:
#         nested_[subj]['have'].add(token)

#     ## other objects, just query the surroundings in knowledge and see which it belongs to
    ## subject-object collocation knowledge ground, subjects in the layerbase
    tokens_copy = tokens_.copy()
    saved_tups = []
    # subjs = [subj for subj in layerbase.collocations_ if subj.t in subjects['surrounding']]
    subjs = [subj for subj in layerbase.collocations_ if Node('have', attr='act') in layerbase.collocations_[subj]]
    for token in tokens_copy:
        tup = find_most_simi_subj(subjs, token)
        if tup:
            subj_, obj_, s_ = tup
            # print(token, obj_, s_, subj_)
            tokens_.remove(token)
            ## use original text in the description as key
            ## or use grounding keyword as key
            # saved_tups.append((subj, token))
            saved_tups.append((subj_, obj_, token))
    for subj, obj, token in saved_tups:
        if MappedToken(None, Node('have', attr='act')) not in nested_[MappedToken(None, subj)]:
            nested_[MappedToken(None, subj)][MappedToken(None, Node('have', attr='act'))] = set()
        nested_[MappedToken(None, subj)][MappedToken(None, Node('have', attr='act'))].add(MappedToken(token, obj))

#         for subj in layerbase.layer_merge_.nested_entities_:
#             if subj not in subjects['surrounding']:
#                 continue
#             for act in layerbase.layer_merge_.nested_entities_[subj]:
#                 obj_ = get_simi_obj(token.lemma_,
#                                     layerbase.layer_merge_.nested_entities_[subj][act],
#                                     thresh=0.3)
#                 if obj_:
#                     assert(act == 'have'), (act, token)
#                     # assert(subj not in [s.lemma_ for s in nested_])
#                     ## Attention! here the key type is string now
#                     print(token, subj, obj_)
#                     tokens_.remove(token)
#                     nested_[subj][act].add(token)
#                     break


# def comb_obj(tokens_, nested_):

#     ## layers built from clusters
#     tokens_copy = tokens_.copy()
#     for token in tokens_copy:

def conj_copy(nested_):
    # subjs = []
    saved_tups = []
    for subj in nested_:
        if subj.token:
            if subj.token.dep_ == 'conj':
                assert(not nested_[subj])
                for subj_ in nested:
                    if subj.token.head == subj_.token and nested_[subj_]:
                        saved_tups.append((subj, subj_))
                        break

    for subj, subj_ in saved_tups:
        nested_[subj] = nested_[subj_]
    # if conj, copy syntactic children

def dup_combine(nested_):
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

def slice_into_layers(nested_):

    # solidify first
    nested_ = ddict2dict(nested_)

    subjs = list(nested_)
    group_list = [[subjs[0]]]
    subjs = subjs[1:]
    while subjs:
        for subj in subjs:
            # for group in group_list:
            matched = [g for g in group_list if subj.token and g[0].token and g[0].token.sent.root==subj.token.sent.root and subj.keyword.t in subjects['character']]
#                 if subj.token.sent.root == group[0].token.sent.root:
#                     group.append(subj)
#                     break
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


####
# technically all entities can be grounded based on similarity, no need to exactly same
####

def ground(filename):
    with open(filename) as f:
        text = f.read()
    print(text.strip('\n'))
    doc = nlp(u'%s' % text.strip('\n'))

    nested = defaultdict(lambda: defaultdict(set))
    tokens = get_tokens(doc)
    print(tokens)
    # map_dict = defaultdict(str)
    ground_subj(tokens, nested)
    # print('-> ground subjects:', ddict2dict(nested))
    # print(tokens)
    ground_act(tokens, nested)
    # print('-> ground actions:', ddict2dict(nested))
    # print(tokens)
    # no verbs will be left
    if not all([t.pos_ != 'VERB' for t in tokens]):
        warnings.warn('Verbs not exhausted!')
        print([t for t in tokens if t.pos_ == 'VERB'])

    # print(tokens)
    ground_obj(tokens, nested)
    if tokens:
        warnings.warn('Tokens not exhausted!')
        print('-> left ungrounded tokens:', tokens)
    dup_combine(nested)
    conj_copy(nested)
    layers = slice_into_layers(nested)
    return layers
