#!./env python
# import glob
# import re

### image encoder
from rules.category import person_dict, surrouding_dict
from tools.common import getNestedKey, getNestedKeyWithCode
from tools.joint_process import wrapRelaxedSimi
from tools.common import flattenNested #, extractLeaf, getDepth
from tools.common import getOrderedList
from tools.image_process import name2code
from tools.joint_process import sentSimi, wrapRelaxedSimi

class BinaryCategEncoder():
    """
    A simple category encoder used for evaluation
    """
    def __init__(self):

        # get feature names
        self.features_ = []
        self.features_.append('_NLayers_')

        # root category features
        self.root_category_ = ['Background', 'Surroundings', 'Person', 'Decoration']
        self.features_.extend(['_%s_' % c for c in self.root_category_])

        # categorical features
        self.srd_categ = getNestedKey(surrouding_dict)
        self.prs_categ = getNestedKey(person_dict)
        self.category_ = self.srd_categ + self.prs_categ
        self.features_.extend(['_S_%s_' % k for k in self.srd_categ])
        self.features_.extend(['_P_%s_' % k for k in self.prs_categ])

    def encode(self, layer_names):

        features = []
        # number of layers
        features.append(len(layer_names))

        features.append(self.rootKey2feature(self.layer2rootKey(layer_names)))
        features.append(self.keyword2feature(self.layer2keyword(layer_names)))

        return np.array(flattenNested(features))

    def layer2rootKey(self, layer_names):
        """
        extract head categories from layer names
        """
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes]
        keys = []
        for i, k in enumerate(self.root_category_):
            if (i+1) in cat_codes:
                keys.append(k)
        return keys

    def rootKey2feature(self, keywords):
        """
        convert root category names to binary features
        """
        return [1 if k in keywords else 0 for k in self.root_category_]
        # return [1 if k in keywords else 0 for k in self.root_category_]

    def keyword2feature(self, keywords):
        """
        Convert category keywords to binary features
        """
        return [1 if k in keywords else 0 for k in self.category_]
        # return [1 if k in keywords else 0 for k in self.category_]

    def layer2keyword(self, layer_names):
        """
        convert layer names to category keywords, but lose the occlusion info
            Person and surrounding only
        """
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes] # head category code

        keywords = []
        for c, dic in zip([2, 3], [surrouding_dict, person_dict]):
            if c in cat_codes:
                subcode = codes[cat_codes.index(c)][1:]
                keywords.extend(getNestedKeyWithCode(dic, subcode))
        return keywords


class CategEncoder():
    def __init__(self, idf=False):

        print('  - Set feature names..')
        # get feature names
        self.features_ = []
        self.features_.append('_NLayers_')

        # root category features
        self.root_category_ = ['Background', 'Surroundings', 'Person', 'Decoration']
        self.features_.extend(['_%s_' % c for c in self.root_category_])
        # self.features_.extend(['_Background_',
        #                        '_Surroundings_',
        #                        '_Person_',
        #                        '_Decoration_'])
                               # '_P_in_front_of_S_',
                               # '_S_in_front_of_P_'])

        # categorical features
        self.srd_categ = getNestedKey(surrouding_dict)
        self.prs_categ = getNestedKey(person_dict)
        self.category_ = self.srd_categ + self.prs_categ
        self.features_.extend(['_S_%s_' % k for k in self.srd_categ])
        self.features_.extend(['_P_%s_' % k for k in self.prs_categ])

        # pair features
        self.features_.extend(['_S_%s-P_%s_' % (ks, kp) for ks in self.srd_categ for kp in self.prs_categ])

        print('  - Build category level idf..')
        idf = True
        # category idf
        if idf:
            from tools.image_process import getLayerNames
            keywords_list = []
            # for img in sorted(glob.glob('images/*.svg'),
            #                   key=lambda img: int(re.findall(r'\d+', img)[0])):
            for img in getOrderedList('images/*.svg'):
                layers = getLayerNames(img)
                keywords_list.append(self.layer2keyword(layers))

            vectorizer = TfidfVectorizer(norm=None,
                                         sublinear_tf=True,
                                         stop_words=[],
                                         lowercase=False,
                                         tokenizer=lambda l: l)
            vectorizer.fit(keywords_list)
            vocab_, _ = zip(*sorted(vectorizer.vocabulary_.items(),
                                    key=lambda x: x[::-1]))
            assert(set(vocab_) == set(self.category_))
            self.idf_ = dict(zip(vocab_, vectorizer.idf_))

            # root idf
            root_keywords_list = []
            # for img in sorted(glob.glob('images/*.svg'),
            #                   key=lambda img: int(re.findall(r'\d+', img)[0])):
            for img in getOrderedList('images/*.svg'):
                layers = getLayerNames(img)
                root_keywords_list.append(self.layer2rootKey(layers))

            root_vectorizer = TfidfVectorizer(norm=None,
                                              sublinear_tf=True,
                                              stop_words=[],
                                              lowercase=False,
                                              tokenizer=lambda l: l)
            root_vectorizer.fit(root_keywords_list)
            vocab_, _ = zip(*sorted(root_vectorizer.vocabulary_.items(),
                                    key=lambda x: x[::-1]))
            assert(set(vocab_) == set(self.root_category_))
            self.root_idf_ = dict(zip(vocab_, root_vectorizer.idf_))

        print('  - Build similarity normalizer..')
        # simi normalizer
        simis = np.array([wrapRelaxedSimi(ks, kp) for ks in self.srd_categ for kp in self.prs_categ])
        self.simi_normalizer = Normalizer()
        self.simi_normalizer.fit(simis)

    def encode(self, layer_names):

        features = []
        # number of layers
        features.append(len(layer_names))

        # convert to digit codes first
        # codes = [name2code(name) for name in layer_names]

        # four types of layers, binary
        # feat_layer = [0] * 4
        # for code in codes:
        #     feat_layer[code[0] - 1] = 1
        # features.append(feat_layer)
        features.append(self.rootKey2feature(self.layer2rootKey(layer_names)))

        """
        Let's resolve the occlusion tentatively.
        The case that surrounding in front of person is too rare and make the reality discriminator too easy.
        The only case that surrounding should be in front of person:
            14.svg
        """
        # # occlusion, person in front of surrounding, or otherwise
        # cat_codes = [code[0] for code in codes]
        # if 2 in cat_codes and 3 in cat_codes:
        #     if cat_codes.index(2) < cat_codes.index(3):
        #         # person in the front
        #         features.append([1,0])
        #     else:
        #         # surrounding in the front
        #         features.append([0,1])
        # else:
        #     features.append([0,0])

        # sub-categories, keyword exists - binary
        ## In fact: one-hot in each level, ensured by the codes
        features.append(self.keyword2feature(self.layer2keyword(layer_names)))

        # cross similarities between subcategories
        features.append(self.crossSimi(layer_names))

        return np.array(flattenNested(features))

    def layer2rootKey(self, layer_names):
        """
        extract head categories from layer names
        """
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes]
        keys = []
        for i, k in enumerate(self.root_category_):
            if (i+1) in cat_codes:
                keys.append(k)
        return keys

    def rootKey2feature(self, keywords):
        """
        convert root category names to binary features
        """
        return [1 * self.root_idf_[k] if k in keywords else 0 for k in self.root_category_]
        # return [1 if k in keywords else 0 for k in self.root_category_]

    def keyword2feature(self, keywords):
        """
        Convert category keywords to binary features
        """
        return [1 * self.idf_[k] if k in keywords else 0 for k in self.category_]
        # return [1 if k in keywords else 0 for k in self.category_]

    def layer2keyword(self, layer_names):
        """
        convert layer names to category keywords, but lose the occlusion info
            Person and surrounding only
        """
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes] # head category code

        keywords = []
        for c, dic in zip([2, 3], [surrouding_dict, person_dict]):
            if c in cat_codes:
                subcode = codes[cat_codes.index(c)][1:]
                keywords.extend(getNestedKeyWithCode(dic, subcode))
        return keywords

    def crossSimi(self, layer_names):
        codes = [name2code(name) for name in layer_names]
        cat_codes = [code[0] for code in codes] # get head category

        srd_keys = []
        if 2 in cat_codes:
            subcode = codes[cat_codes.index(2)][1:]
            srd_keys = getNestedKeyWithCode(surrouding_dict, subcode)

        prs_keys = []
        if 3 in cat_codes:
            subcode = codes[cat_codes.index(3)][1:]
            prs_keys = getNestedKeyWithCode(person_dict, subcode)

        # return [wrapRelaxedSimi(ks, kp) if ks in srd_keys and kp in prs_keys else 0 for ks in self.srd_categ for kp in self.prs_categ]
        # return [self.idf_[ks] * self.idf_[kp] * wrapRelaxedSimi(ks, kp) if ks in srd_keys and kp in prs_keys else 0 for ks in self.srd_categ for kp in self.prs_categ]
        ## using normalized similarities yields similar performance
        # return [self.simi_normalizer.transform(wrapRelaxedSimi(ks, kp)) if ks in srd_keys and kp in prs_keys else 0 for ks in self.srd_categ for kp in self.prs_categ]
        return [self.idf_[ks] * self.idf_[kp] * self.simi_normalizer.transform(wrapRelaxedSimi(ks, kp)) if ks in srd_keys and kp in prs_keys else 0 for ks in self.srd_categ for kp in self.prs_categ]


### text encoder
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from tools.text_process import LemmaTokenizer

class TfidfEncoder():
    def __init__(self, txt_dir='text'):
        ## tokenizer
        self.tokenizer = LemmaTokenizer()
        corpus = []
        # for fileName in sorted(glob.glob('text/*.txt')):
        for fileName in getOrderedList('text/*.txt'):
            with open(fileName, 'r') as f:
                sent = f.read()
                tokens = self.tokenizer(sent)
                corpus.append(tokens)

        ## vectorizer
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2),
                                          norm=None,
                                          sublinear_tf=True,
                                          stop_words=[],
                                          lowercase=False,
                                          tokenizer=lambda l: l)
        self.vectorizer.fit(corpus)

        ## features
        self.vocab_, _ = zip(*sorted(self.vectorizer.vocabulary_.items(),
                                     key=lambda x:x[::-1]))

        # idf dict
        self.idf_ = dict(zip(self.vocab_, self.vectorizer.idf_))

    def encode(self, sentence):
        assert(isinstance(sentence, str))
        tokens = self.tokenizer(sentence)
        return self.vectorizer.transform([tokens]).toarray()[0]


### joint encoder
import numpy as np
from scipy import sparse
from tools.common import Normalizer

class SimiEncoder():
    def __init__(self, img_encoder, txt_encoder):
        self.img_encoder = img_encoder
        self.txt_encoder = txt_encoder

        # set features
        ### be extremely careful here for the order of feature names
        self.features_ = []
        self.features_.extend(['_S_%s-%s_' % (k, t) for k in img_encoder.srd_categ for t in txt_encoder.vocab_])
        self.features_.extend(['_P_%s-%s_' % (k, t) for k in img_encoder.prs_categ for t in txt_encoder.vocab_])

        # simi dict
        simis = [wrapRelaxedSimi(k, t) for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_]
        self.simi_ = dict(zip(self.features_, simis))

        # simi normalizer
        # simis = np.array([wrapRelaxedSimi(k, t) for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_ if len(t.split()) == 1])
        self.simi_normalizer = Normalizer()
        # self.simi_normalizer.fit(simis)
        ## should we filter out 0? yep, too many 0, otherwise normalize takes no effects
        ### filtering out 0 strongly reduces the performance
        self.simi_normalizer.fit([s for s in simis if s != 0])

    def encode(self, layer_names, sentence):
        assert(isinstance(layer_names, list))
        assert(isinstance(layer_names[0], str))
        assert(layer_names[0].startswith('A'))
        assert(isinstance(sentence, str))

        keywords = self.img_encoder.layer2keyword(layer_names)
        tokens = self.txt_encoder.tokenizer(sentence)
        # return np.array(flattenNested([sentSimi(tokens, k, self.txt_encoder.vocab_) if k in keywords else sentSimi(tokens, None, self.txt_encoder.vocab_) for k in self.img_encoder.category_]))
        # return np.array([1 if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])
        # return np.array([self.txt_encoder.idf_[t] if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])
        return np.array([self.txt_encoder.idf_[t] * self.simi_normalizer.transform(wrapRelaxedSimi(k, t)) if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])
                ## - fix this dict - tell P and S - speed up
                ## but need to differ P and S, put it up
        ## return np.array([self.idf_[t] * self.simi_normalizer.transform(self.simi_) if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])
        # return np.array([self.idf_[t] * wrapRelaxedSimi(k, t) if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])
        # return np.array([wrapRelaxedSimi(k, t) if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])
        # return np.array([self.txt_encoder.idf_[t] * self.img_encoder.idf_[k] * self.simi_normalizer.transform(wrapRelaxedSimi(k, t)) if k in keywords and t in tokens else 0 for k in self.img_encoder.category_ for t in self.txt_encoder.vocab_])



