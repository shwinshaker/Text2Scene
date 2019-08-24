#!./env python

from scipy import sparse
import numpy as np
import glob
from sklearn.linear_model import LogisticRegression

### sparse matrix
def sparse_shuffle(X, interval=1):
    assert(isinstance(X, sparse.csr.csr_matrix))

    index_split = np.array_split(np.arange(X.shape[0]), X.shape[0]/interval)
    np.random.shuffle(index_split)
    ran_index = np.hstack(index_split)
    return X[ran_index], ran_index

def prep_data(Dataset, index_tup=None, test=0.1, shuffle=True, seed=7, **kwargs):
        # shuffle_interval=1):

    if index_tup is None:
        index = [i+1 for i in range(len(glob.glob('images/*.svg')))]

        if seed:
            np.random.seed(seed)

        if shuffle:
            np.random.shuffle(index)

        ind_ = int(len(index) * (1-test))
        index_train = index[:ind_]
        index_test = index[ind_:]
    else:
        assert(isinstance(index_tup, tuple)), 'Plz provide train and test indexes.'
        index_train, index_test = index_tup

    print(' - Preparing data..')
    dataset = Dataset(index=index_train, **kwargs)
    dataset.index_train = index_train
    dataset.index_test= index_test
    # print('# features: ', len(dataset.features_))

    def __fetch_data(index):
        data = []
        pairs = []
        for c, i in enumerate(index):
            print('    Fetching - [%i]' % c, end='\r')
            vec, pair = dataset[i-1] # follow the 0-start convention
            data.append(vec)
            pairs.extend(pair)
        print('     Fetched - [%i]' % (c+1))
        data = sparse.vstack(data)
        return data, pairs

    print('- Fetching training data..')
    dataset.data_train, dataset.data_train_pairs = __fetch_data(dataset.index_train)
    print('- Fetching test data..')
    dataset.data_test, dataset.data_test_pairs = __fetch_data(dataset.index_test)
    print('  - Data train shape', dataset.data_train.shape)
    print('  - Data test shape', dataset.data_test.shape)

    ## recall can be very high if not shuffle the data, why?
    # data, index = sparse_shuffle(data, interval=shuffle_interval)
    ## print(index, pairs)
    # pairs = [pairs[ind] for ind in index]
    # X, y = data[:,:-1], data[:,-1]
    # y = y.toarray().flatten()
    # return dataset, X, y, pairs, index
    return dataset

def train_classifier(dataset, class_weight=None, C=1.0):
    clf = LogisticRegression(# random_state=0,
                             solver='liblinear',
                             class_weight=class_weight,
                             penalty='l1',
                             C=C,
                             max_iter=1000)

    clf.fit(dataset.data_train[:,:-1],
            dataset.data_train[:,-1].toarray().flatten())
    return clf
