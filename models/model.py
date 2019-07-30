#!./env python

import dill
import numpy as np

class Discriminator():
    def __init__(self, dataset, clf, dataset_r, clf_r):
        self.dataset = dataset
        self.dataset_r = dataset_r
        self.clf = clf
        self.clf_r = clf_r

    @staticmethod
    def unpickle():
        with open('results/discriminator.pkl', 'rb') as f:
           return dill.load(f)

def exhaustiveSearch(query_txt, discriminator, lamb=0.7):
    probs = []
    for i, layers in enumerate(discriminator.dataset.all_layers):
        print('Searching.. [%i]' % i, end='\r')
        X = discriminator.dataset.encode(sent=query_txt, layers=layers)
        prob_consis = np.squeeze(discriminator.clf.predict_proba(X.reshape(1,-1)))[1]
        X_r = discriminator.dataset_r.img_encoder.encode(layers)
        prob_real = np.squeeze(discriminator.clf_r.predict_proba(X_r.reshape(1,-1)))[1]
        probs.append((i, prob_consis*lamb + prob_real*(1-lamb)))

    ## only probs, i.e. losses acts here
    ## thus the prediction doesn't depend on the threshold
    imax, max_prob = max(probs, key=lambda x: x[1])
    max_layers = discriminator.dataset.all_layers[imax]

    return max_layers, max_prob


def categPrecision(discriminator, layers, sentence, lamb=0.5, verbose=False):

    tokens = discriminator.dataset.txt_encoder.tokenizer(sentence)
    pred_layers, prob = exhaustiveSearch(sentence,
                                         discriminator,
                                         lamb=lamb)

    from models.encoder import BinaryCategEncoder
    encoder = BinaryCategEncoder()
    embed_true = encoder.encode(layers)[1:]
    embed_pred = encoder.encode(pred_layers)[1:]

    from ana.visual import _acc, _precision, _recall, _F1
    assert(len(embed_pred) == 4 + 16 + 17)
    acc = _acc(embed_true, embed_pred)
    precision = _precision(embed_true, embed_pred)
    recall = _recall(embed_true, embed_pred)
    F1 = _F1(precision, recall)

    if verbose:
        print('Keywords: ', discriminator.dataset.img_encoder.layer2keyword(layers))
        print('Sentence: %s' % sentence)
        print('Tokens:', tokens)
        seen_tokens = []
        for token in tokens:
            if token in discriminator.dataset.txt_encoder.vocab_:
                seen_tokens.append(token)
        print('Seen tokens:', seen_tokens)
        # print('\nMost consistent layer:', pred_layers)
        print('\nPredicted keywords:', discriminator.dataset.img_encoder.layer2keyword(pred_layers), 'Prob: %.6f' % prob)
        print('Acc: %.6f - Precision: %.6f - Recall: %.6f - F1: %.6f' % (acc, precision, recall, F1))

    return acc, F1


def categMetric(discriminator, index=None, test_num=5, lamb=1.0):
    if index is None:
        # import random
        # index = list(range(len(discriminator.dataset)))
        # random.shuffle(index)
        # index = index[:test_num]
        index = discriminator.dataset.index_test

    assert(lamb <= 1 and lamb >= 0)

    F1s = []
    for c, i in enumerate(index):
        img = 'images/%i.svg' % i
        txt = 'text/%i.txt' % i
        acc, F1 = categPrecision(discriminator,
                                 *discriminator.dataset.getOneLayerSent(txt, img),
                                 lamb=lamb, verbose=False)
        print('%i-----------' % c)
        F1s.append(F1)
    mF1 = sum(F1s)/len(F1s)
    print('mean F1: %.6f' % mF1)

    return mF1
