#!./env python

from tools.knowledge import LayerBase
from rules.labels import subjects
from tools.image_process import getSubj
from tools.containers import Picture

import itertools
import random

# the frequency should be based on priors
def exhaustivePicGenerator(layerbase, beam={'background': 2,
                                            'surrounding': 10,
                                            'character': 10,
                                            'accessory': 2}, verbose=True):
    # layerbase = LayerBase()

    comb_dic = {}
    comb_dic['background'] = ['#background', '']
    comb_dic['surrounding'] = [str(l) for l in layerbase.layer_vocab_ if getSubj(str(l)) in subjects['surrounding']] + ['']
    comb_dic['character'] = [str(l) for l in layerbase.layer_vocab_ if getSubj(str(l)) in subjects['character']] + ['']
    comb_dic['accessory'] = [str(l) for l in layerbase.layer_vocab_ if getSubj(str(l)) == 'accessory'] + ['']
    # comb_dic['accessory'] = ['#accessory', '']

    li = []
    for key in comb_dic:
        assert(beam[key] <= len(comb_dic[key])), (beam[key], len(comb_dic[key]))
        layers_ = comb_dic[key].copy()
        random.shuffle(layers_)
        li.append(layers_[:beam[key]])

    # combs = list(itertools.product(*tuple(comb_dic.values())))
    combs = list(itertools.product(*tuple(li)))

    if verbose:
        for categ in comb_dic:
            print(categ, len(comb_dic[categ]))
        print('combs', len(combs))

    def to_list_of_layernames(tup):
        return [t for t in tup if t]

    for i, t in enumerate(combs):
        print('[%i]' % i, end='\r')
        layernames = to_list_of_layernames(t)
        if layernames:
            yield Picture(layernames=layernames)
