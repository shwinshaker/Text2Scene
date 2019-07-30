#!./env python

import numpy as np
import random
np.random.seed(6)
random.seed(7)

from models.dataset import Dataset, DatasetReality
from models.pipeline import prep_data
from ana.visual import STAT, ROC, FEAT
from sklearn.linear_model import LogisticRegression

import warnings
warnings.simplefilter('ignore')


print('\n> preparing dataset..')
dataset_r, X_r, y_r, pairs_r, index_r = prep_data(DatasetReality, shuffle_interval=2)

print('\n> training..')
clf_r = LogisticRegression(# random_state=0,
                           solver='liblinear',
                           class_weight={1: 1, 0: 1},
                           penalty='l1', #'l2' use l1 to learn sparsely
                           C=1.0,
                           max_iter=1000)

interval = 2
ind_test = int(X_r.shape[0]/interval * 0.9) * interval
print('# train: ', ind_test)
print('# test: ', X_r.shape[0] - ind_test)
clf_r.fit(X_r[:ind_test], y_r[:ind_test])

print('\n> evaluation..')
y_true = y_r[ind_test:]
y_prob = clf_r.predict_proba(X_r[ind_test:])[:,1]

# analysis
suffix = 'temp2'
STAT(y_true, y_prob, path='realitySTAT_%s' % suffix)
ROC(y_true, y_prob, path='realityROC_%s' % suffix)
FEAT(dataset_r, clf_r, path='realityFEAT_%s' % suffix)
