#!./env python

from lib.tools.image_process import stack_svgs
from lib.models.predictor import Predict1
import argparse

# initialize predictor
predict = Predict1(img_dir='dataset/images')

# arguments
parser = argparse.ArgumentParser()
parser.add_argument(dest='query', metavar='Query', type=str, help='A query sentence')
args = parser.parse_args()
print('Given input:')
print(args.query)

# retrieve and stack materials
materials = ['dataset/material/%s.png' % l.s for l in predict(args.query)]
if not materials:
    print('Generation error! No material is retrieved!')
else:
    stack_svgs(materials)
    print('\noutput to ./stack.svg')
