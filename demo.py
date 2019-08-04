#!./env python

from models.model import Discriminator, exhaustiveSearch
from tools.image_process import stack_svgs
from tools.common import getMaterial

discriminator = Discriminator.unpickle()
layers, prob = exhaustiveSearch('A man is showing a chart.',
                                 discriminator,
                                 lamb=0.8)
print('layers: ', layers)
print('prob: %.6f' % prob, end='\n\n')
stack_svgs([getMaterial(layer) for layer in layers])
print('\n output to stack.svg')
