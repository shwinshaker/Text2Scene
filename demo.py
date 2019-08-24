#!./env python

# from models.model import Discriminator, exhaustiveSearch
from tools.image_process import stack_svgs
# from tools.common import getMaterial
import argparse
from models.pipeline import Translate

parser = argparse.ArgumentParser()
parser.add_argument(dest='query', metavar='Query', type=str, help='A query sentence')
# parser.add_argument('--lambda', dest='lamb', default=0.8, type=float, help='the weight between discriminators (default: 0.8)')

args = parser.parse_args()
# translate = Translate(img_dir='images_train')
translate = Translate(img_dir='images')
# print(args.lamb, type(args.lamb))
# discriminator = Discriminator.unpickle(model_path='results/discriminator1.pkl')
# layers, prob = exhaustiveSearch(args.query, discriminator, lamb=args.lamb)
# print('layers: ', layers)
# print('prob: %.6f' % prob, end='\n\n')
# stack_svgs([getMaterial(layer) for layer in layers])
print(args.query)
materials = ['material/%s.png' % l.s for l in translate(args.query)]
if not materials:
    print('Generation error! No material is retrieved!')
else:
    stack_svgs(materials)
    print('\n output to stack.svg')
