#!./env python

from ..tools.containers import Picture
class Predict:
    def __init__(self, **kwargs):
        pass

    def __call__(self, text):
        return Picture()


from .parser import GraphParser
from .components import KeywordGrounder, GraphManipulator, LayerSlicer, LayerGround
from ..tools.knowledge import VocabBase
from ..tools.containers import GraphSpan

class Predict1(Predict):

    @staticmethod
    def help():
        print("""
Generator: graph based generator with heuristic combinations
Discriminator: handcrafted consistency and reasonability score
""")

    def __init__(self, **kwargs):

        ### layerbase knowledge
        self.vocabbase = VocabBase(**kwargs)
        ### graph parser
        self.parser = GraphParser()
        ### keyword ground
        self.keywordground = KeywordGrounder(self.vocabbase)
        ### graph extension
        self.extend = GraphManipulator()
        ### slice graph into layers
        self.slice = LayerSlicer()
        ### layer ground
        self.layerground = LayerGround(self.vocabbase)

    def __score(self, cons, reas, lamb=0.8):
        return cons*lamb + reas*(1-lamb)

    def __call__(self, text, extend=True, top=1, with_graph=False):
        # self.text = text
        G = self.parser(text)
        H = self.keywordground(G)
        H_ = GraphSpan(H)
        graphs = [H_]
        if extend:
            graphs = self.extend(H_)

        gen_pics = []
        for graph in graphs:
            for pic in self.slice(graph):
                gen_pic = self.layerground(pic)
                gen_pics.append(gen_pic + (pic,) + (graph,))
        gen_pics = sorted(gen_pics, key=lambda x: self.__score(x[1], x[2]))[::-1]
        print(gen_pics[0][-2]) # .layer_merge_.nested_entities_)
        if top > 1:
            num = min(top, len(gen_pics))
            if with_graph:
                return [gen_pics[i][0] for i in range(num)], [gen_pics[i][-1] for i in range(num)]
            return [gen_pics[i][0] for i in range(num)]
        if with_graph:
            return gen_pics[0][0], gen_pics[0][-1]
        return gen_pics[0][0]


from .generator import exhaustivePicGenerator
from .dataset import Dataset
from ..tools.common import getBase
from ..tools.containers import Description
from scipy import sparse
import glob

class Predict2(Predict):

    @staticmethod
    def help():
        print("""
Generator: beam search of combinations of layers
Discriminator: score network trained on histograms of keyword-token similarities
""")

    def __init__(self, beam=None, evaluate_discriminator=False,
                 train_path='dataset/images_train',
                 test_path='dataset/images_val'):
        if not beam:
            self.beam = {'background': 2,
                         'surrounding': 20,
                         'character': 20,
                         'accessory': 2}

        print(' ------ train test split -------')
        self.train_names, self.test_names = self.train_test_split(train_path, test_path)

        print(' ------ build dataset -------')
        self.dataset = Dataset(names=self.train_names)

        print(' ------ gather data -------')

        # self.train_set, self.test_set =
        self.build_data(self.train_names,self.test_names)

        print(' ------ train and evaluation -------')
        self.clf = self.train(self.train_set)
        if evaluate_discriminator:
            self.evaluate(self.clf, self.train_set, self.test_set)

#     def train_test_split(self, test_r=0.2, shuffle=True):
#         names = [getBase(path) for path in glob.glob('dataset/images/*.svg')]
#         names_ = [getBase(path) for path in glob.glob('dataset/text/*.txt')]

#         # names must be unique
#         assert(len(names) == len(set(names)))
#         # names from both sides must be identical
#         assert(set(names) == set(names_))

#         if shuffle:
#             random.shuffle(names)

#         ind = int(len(names) * (1-test_r))

#         return names[:ind], names[ind:]

    def train_test_split(self, train_path, test_path):
        """
        use fixed train and test set
        """
        train = [getBase(path) for path in glob.glob(train_path)]
        test = [getBase(path) for path in glob.glob(test_path)]

        return train, test

    def __fetch_data(self, names):
        data = []
        pairs = []
        for c, name in enumerate(names):
            print('    Fetching: [%i] - %s' % (c, name), end='\r')
            vec, pair = self.dataset[name]
            data.append(vec)
            pairs.extend(pair)
        print('     Fetched: [%i]' % (c+1))
        data = sparse.vstack(data)
        return data, pairs

    def build_data(self, train, test):

        print(' -------------- train set ---------------- ')
        self.train_set, self.train_pairs = self.__fetch_data(train) # np.vstack(train_set)

        print(' -------------- test set ---------------- ')
        # test_set = np.vstack([self.dataset[name] for name in test])
        self.test_set, self.test_pairs = self.__fetch_data(test)
        # return train_set, test_set

    def train(self, train_set, class_weight={1: 1, 0: 0.1}, C=1.0):
        from sklearn.linear_model import LogisticRegression

        clf = LogisticRegression(# random_state=0,
                         solver='liblinear',
                         class_weight=class_weight,
                         penalty='l1',
                         C=C,
                         max_iter=100)

        clf.fit(train_set[:,:-1],
                train_set[:,-1].toarray().flatten())
        return clf

    def evaluate(self, clf, train_set, test_set,
                 save=False, suffix='temp'):

        from ana.visual import STAT, ROC, FEAT

        print('------- train ---------')
        y_true = train_set[:,-1].toarray().flatten()
        y_prob = clf.predict_proba(train_set[:,:-1])[:,1]
        STAT(y_true, y_prob, save=save)

        print('------- test ---------')
        y_true = test_set[:,-1].toarray().flatten()
        y_prob = clf.predict_proba(test_set[:,:-1])[:,1]

        print('-- visual --')
        STAT(y_true, y_prob, save=save)
        ROC(y_true, y_prob, save=save)
        FEAT(self.dataset, clf, save=save, top=20)

    def generator(self, verbose=False):
        return exhaustivePicGenerator(self.dataset.encoder.layerbase,
                                      beam=self.beam,
                                      verbose=verbose)

    def __call__(self, text, verbose=False):

        doc = Description(text=text)
        gen_pics = []
        for pic in self.generator():
            vec = self.dataset.encoder.encode(doc, pic)
            gen_pics.append((pic, self.clf.predict_proba([vec])[0,1]))
        gen_pics = sorted(gen_pics, key=lambda x: x[1])[::-1]
        return gen_pics[0][0]


class Predict3(Predict):

    @staticmethod
    def help():
        print("""
Generator: graph based generator with heuristic combinations
Discriminator: score network trained on histograms of keyword-token similarities
""")

    def __init__(self, **kwargs):

        ### layerbase knowledge
        self.vocabbase = VocabBase(**kwargs)
        ### graph parser
        self.parser = GraphParser()
        ### keyword ground
        self.keywordground = KeywordGrounder(self.vocabbase)
        ### layer ground
        self.layerground = LayerGround(self.vocabbase)

    def __score(self, prob):
        return prob

    def __call__(self, text):
        doc = Description(text=text)

        G = self.parser(text)
        H = self.keywordground(G)
        H_ = GraphSpan(H)
        picture_generator = LayerSlicer(H_).get_generator()
        gen_pics = []
        for pic in picture_generator:
            gen_pic = self.layerground(pic)[0]
            vec = pipeline.dataset.encoder.encode(doc, gen_pic)
            gen_pics.append((gen_pic, pipeline.clf.predict_proba([vec])[0,1]))
        gen_pics = sorted(gen_pics, key=lambda x: self.__score(x[1]))[::-1]
        return gen_pics[0][0]
        # sorted(probas, key=lambda x: x[1])[-1][0]



