#!./env python

from tools.image_process import stack_svgs
import argparse
from models.predictor import Predict1

# initialize predictor
predict = Predict1()

# arguments
parser = argparse.ArgumentParser()
parser.add_argument(dest='query', metavar='Query', type=str, help='A query sentence')
args = parser.parse_args()
print(args.query)

# retrieve and stack materials
materials = ['material/%s.png' % l.s for l in predict(args.query)]
if not materials:
    print('Generation error! No material is retrieved!')
else:
    stack_svgs(materials)
    print('\n output to stack.svg')
