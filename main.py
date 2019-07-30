#!./env python

# from models.encoder import *
## why must we need this class be imported?
from tools.text_process import LemmaTokenizer

from models.model import Discriminator
from models.model import categMetric

import warnings
warnings.simplefilter('ignore')

discriminator = Discriminator.unpickle()
categMetric(discriminator, lamb=1.0)
