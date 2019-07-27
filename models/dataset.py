#!./env python
import numpy as np
import glob
import random
from scipy import sparse

from models.encoder import TfidfEncoder, CategEncoder, SimiEncoder
from tools.image_process import getLayerNames

# random image generator, subject to rules
from tools.generator import ranGenLayer, getAllLayerCombs

class Dataset():
    def __init__(self, img_dir='images', txt_dir='text'):
        self.img_dir = img_dir
        self.txt_dir = txt_dir

        # fitting the vectorizer will process all the text
        # so we have double processed the text here
        self.img_encoder = CategEncoder()
        self.txt_encoder = TfidfEncoder()
        self.joint_encoder = SimiEncoder(self.img_encoder,
                                         self.txt_encoder)

        # set features
        self.features_ = []
        self.features_.extend(self.txt_encoder.vocab_)
        self.features_.extend(self.img_encoder.features_)
        self.features_.extend(self.joint_encoder.features_)

        # all possible layers: for check
        self.all_layers = getAllLayerCombs()

    def getOneLayerSent(self, txt_name=None, img_name=None,
                              ran_txt=False, ran_img=False,
                              fake_img=False):
        ##### preprocess
        ## text
        if ran_txt:
            all_txt = glob.glob(self.txt_dir+'/*.txt')
            # rule out current text
            all_txt.remove(txt_name)
            txt_name = random.choice(all_txt)
        else:
            assert(txt_name)

        with open(txt_name, 'r') as f:
            sent = f.read()

        ## image
        if ran_img:
            assert img_name
            assert not fake_img
            all_img = glob.glob(self.img_dir+'/*.svg')
            all_img.remove(img_name)
            img_name = random.choice(all_img)
            layers = getLayerNames(img_name)
        elif fake_img:
            assert img_name is None
            assert not ran_img
            layers = self.getFakeLayers()
        else:
            layers = getLayerNames(img_name)

        return layers, sent

    def encode(self, layers=None, sent=None, **kwargs):
        assert((layers and sent) or (not layers and not sent)), 'layers and sentence must be provided together, or neither'

        if not layers and not sent:
            layers, sent = self.getOneLayerSent(**kwargs)

        assert(layers in self.all_layers), ('layer not identified!', layers)

        # tofeature
        txt_embed = self.txt_encoder.encode(sent)
        img_embed = self.img_encoder.encode(layers)
        joint_embed = self.joint_encoder.encode(layers, sent)

        return np.hstack([txt_embed, img_embed, joint_embed])

    def __getitem__(self, ind):
        img_name = '%s/%i.svg' % (self.img_dir, ind+1)
        txt_name = '%s/%i.txt' % (self.txt_dir, ind+1)

        # triplets
        triplets = []
        # true match
        triplets.append(self.encode(txt_name=txt_name,
                                    img_name=img_name))
#         # fake image
#         triplets.append(self.encode(txt_name=txt_name,
#                                     fake_img=True))
        # mismatched text
        triplets.append(self.encode(img_name=img_name,
                                    txt_name=txt_name,
                                    ran_txt=True))
        # mismatched image
        triplets.append(self.encode(img_name=img_name,
                                    txt_name=txt_name,
                                    ran_img=True))

        xs = np.vstack(triplets)

        # ys
        # ys = np.array([1,0,0,0]).reshape(-1,1)
        ys = np.array([1,0,0]).reshape(-1,1)

        return sparse.csr_matrix(np.hstack([xs, ys]))

    def getFakeLayers(self):
        return ranGenLayer()

    def __len__(self):
        return len(glob.glob(self.img_dir+'/*.svg'))


class DatasetReality(Dataset):
    """
    Dataset used to discriminate real images and fake images
    """
    def __init__(self):
        super().__init__()

        # all layers that appeared
        all_imgs = glob.glob(self.img_dir+'/*.svg')
        self.true_layers = [getLayerNames(img) for img in all_imgs]
        self.fake_layers = self.__list_diff(self.all_layers,
                                            self.true_layers)

        # features
        self.features_ = self.img_encoder.features_

    def __list_diff(self, all_, true):
        true = set([tuple(l) for l in true])
        all_ = set([tuple(l) for l in all_])
        fake = [list(l) for l in all_ - true]
        assert(len(fake) == len(all_) - len(true))
        return fake

    def __getitem__(self, ind):
        img_name = '%s/%i.svg' % (self.img_dir, ind+1)

        # pairs
        pairs = []

        # true image
        layers = getLayerNames(img_name)
        pairs.append(self.img_encoder.encode(layers))

        # fake image
        fake_layers = self.getFakeLayers()
        pairs.append(self.img_encoder.encode(fake_layers))

        xs = np.vstack(pairs)

        # ys
        ys = np.array([1,0]).reshape(-1,1)

        return sparse.csr_matrix(np.hstack([xs, ys]))

    def getFakeLayers(self):
        """
        rewrite the fake generation
            choose from layers not appeared
        """
        return random.choice(self.fake_layers)