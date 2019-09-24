#!./env python

from scipy import sparse
import numpy as np
import pickle
from sklearn.preprocessing import MinMaxScaler
from ..tools.knowledge import LayerBase, TextBase
from ..tools.containers import Description, Picture
from ..tools.common import enableQuery, enableQuery_

# temporarily set to 0
@enableQuery_
class TextPictureRavelHistSimiEncoder:
    """
    IDF?
        E.g. man and woman are everywhere
    """
    def __init__(self, names=[], length=5):

        # feature length
        self.length = length

        print(' - Initiate layer base..')
        ## layerbase can utilize the entire dataset, why is that?
        # self.layerbase = LayerBase()
        self.layerbase = LayerBase(names)
        print(' - Initiate text base..')
        self.textbase = TextBase(names)

        assert(length < len(self.textbase)), 'feature length should be smaller than the textbase length %i' % len(self.textbase)

        print(' - Initiate scaler..')
        self.scaler = MinMaxScaler()
        self.scaler.fit(np.array([self.query_simi(k.t, t.t) for k in self.layerbase.vocab_ for t in self.textbase.vocab_]).reshape(-1,1))

        # bins = np.linspace(0, 1, num+1)
        # extra bin to make the right one open to filter zeros
        self.bins = np.arange(0, 1 + 2/length, 1/length)

        print(' - List feature names..')
        str_bins = ['(%g,%g]' % tup for tup in zip(self.bins[:-2], self.bins[1:-1])]
        self.features_ = ['_%s_%s_' % (k, b) for k in self.layerbase.vocab_ for b in str_bins]

    def encode(self, doc, pic):
        # tokens or keywords should contain no duplicates
        assert(isinstance(doc, Description))
        assert(isinstance(pic, Picture))

        # record the input for share
        self.tokens = doc.vocab_
        self.keywords = pic.vocab_

        # print(' -- gen sparse..')
        tuples = []
        for token in doc.vocab_:
            if token not in self.textbase:
                warnings.warn('Unseen word encountered! %s(%s)' % (token.t, token.attr))
                continue
            for keyword in pic.vocab_:
                if keyword not in self.layerbase:
                    warnings.warn('Unseen keyword encountered! %s(%s)' % (keyword.t, keyword.attr))
                    continue
                tuples.append((self.layerbase.index(keyword),
                               self.textbase.index(token),
                               self.query_simi(keyword.t, token.t)))
        if not tuples:
            warnings.warn('No word in \"%s\" are seen. Returned zero matrix.' % doc.text_.strip('\n'))
            return np.zeros((len(self.layerbase), self.length)).ravel()

        row, col, data = zip(*tuples)

        # print(' -- scale..')
        data = self.scaler.transform(np.array(data).reshape(-1,1)).ravel()

        assert(min(data) >= 0), min(data)
        assert(max(data) <= 1), max(data)

        # scipy sparse unexpected doubles some value
        # because there are duplicate tokens in the token list
        # turn it into set
        matrix = sparse.csr_matrix((data, (row, col)),
                                    shape=(len(self.layerbase),
                                           len(self.textbase)))

        # print(' -- gen hists..')
        return self.to_hists(matrix).ravel()

    def to_hists(self, matrix):

        assert(isinstance(matrix, sparse.csr_matrix))
        # assert(isinstance(matrix, np.ndarray))
        assert(len(matrix.shape) == 2)
        assert(matrix.min()>=0), matrix.min()
        assert(matrix.max()<=1), matrix.max()

        # such that the bins are lefthand open. E.g. (0,0.2]
        arr = 1 - matrix.toarray()
        hists = []
        for row in range(arr.shape[0]):
            # [:-1]: clip the stats of zeros in the hists
            hist = np.histogram(arr[row], self.bins)[0][::-1][1:]
            assert(sum(hist) <= len(self.tokens))
            hists.append(hist)
        return np.vstack(hists)

    def show_hists(self, vec):
        """
        bind no-zeros rows to layer keywords to check sanity
        """
        for line in filter(lambda x: sum(x[0])>0, list(zip(vec, self.layerbase.vocab_))):
            print(line)

