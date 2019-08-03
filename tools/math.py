#!./env python

import numpy as np

class Normalizer():
    """
    A transformer used for standard normalization
    """
    def __init__(self):
        pass

    def fit(self, x):
        self.mean = np.mean(x)
        self.std = np.std(x)

    def transform(self, x):
        return (x - self.mean) / self.std

def sigmoid(x):
    return 1/(1+np.exp(-x))
