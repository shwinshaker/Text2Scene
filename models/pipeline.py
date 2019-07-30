#!./env python

from scipy import sparse
import numpy as np

### sparse matrix
def sparse_shuffle(X, interval=1):
    assert(isinstance(X, sparse.csr.csr_matrix))

    index_split = np.array_split(np.arange(X.shape[0]), X.shape[0]/interval)
    np.random.shuffle(index_split)
    ran_index = np.hstack(index_split)
    return X[ran_index], ran_index

def prep_data(Dataset, index=None, test=0.1, shuffle=True, seed=7):
        # shuffle_interval=1):
    dataset = Dataset()
    # print('# features: ', len(dataset.features_))
    print(' - Preparing data..')

    if index is None:
        index = list(range(len(dataset)))

        if seed:
            np.random.seed(seed)

        if shuffle:
            np.random.shuffle(index)

        dataset.index = index
        ind_ = int(len(index) * (1-test))
        dataset.index_train = index[:ind_]
        dataset.index_test = index[ind_:]
    else:
        assert(isinstance(index, tuple)), 'Plz provide train and test indexes.'
        dataset.index_train, dataset.index_test = index

    def __fetch_data(index):
        data = []
        pairs = []
        for c, i in enumerate(index):
            print('    Fetching - [%i]' % c, end='\r')
            vec, pair = dataset[i]
            data.append(vec)
            pairs.extend(pair)
        print('    Fetched - [%i]' % (c+1))
        data = sparse.vstack(data)
        return data, pairs

    dataset.data_train, dataset.data_train_pairs = __fetch_data(dataset.index_train)
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
