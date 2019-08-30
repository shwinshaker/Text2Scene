#!./env python
import numpy as np
# import glob
import random
from scipy import sparse

from models.encoder import TfidfEncoder, CategEncoder, SimiEncoder
from tools.image_process import getLayerNames
from tools.common import getFiles #getOrderedList

# random image generator, subject to rules
from tools.generator import ranGenLayer, getAllLayerCombs

class Dataset():
    def __init__(self, img_dir='images', txt_dir='text',
                                         index=None,
                                         text_idf=True,
                                         categ_idf=True,
                                         cross_simi=True,
                                         norm_simi=True,
                                         suppress_freq=3):
        self.img_dir = img_dir
        self.txt_dir = txt_dir
        self.index = index

        # fitting the vectorizer will process all the text
        # so we have double processed the text here
        print(' - Initialize image encoder..')
        self.img_encoder = CategEncoder(index=index,
                                        idf=categ_idf,
                                        # simi=cross_simi,
                                        # suppress_freq=suppress_freq,
                                        norm_simi=norm_simi)
        print(' - Initialize text encoder..')
        self.txt_encoder = TfidfEncoder(index=index)
        print(' - Initialize joint encoder..')
        self.joint_encoder = SimiEncoder(self.img_encoder,
                                         self.txt_encoder,
                                         text_idf=text_idf,
                                         categ_idf=categ_idf,
                                         simi=cross_simi,
                                         norm_simi=norm_simi,
                                         suppress_freq=suppress_freq)

        # set features
        print(' - Set feature names..')
        self.features_ = []
        self.features_.extend(self.txt_encoder.vocab_)
        self.features_.extend(self.img_encoder.features_)
        self.features_.extend(self.joint_encoder.features_)

        # get all possible combinations of layers: for check
        self.all_layers = getAllLayerCombs()

    def getOneLayerSent(self, txt_name=None, img_name=None,
                              ran_txt=False, ran_img=False,
                              fake_img=False):
        ##### preprocess
        ## text
        if ran_txt:
            # all_txt = glob.glob(self.txt_dir+'/*.txt')
            # all_txt = list(getOrderedList(self.txt_dir+'/*.txt'))
            all_txt = list(getFiles(self.txt_dir, ext='.txt', index=self.index))
            # rule out current text
            if txt_name in all_txt:
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
            # all_img = glob.glob(self.img_dir+'/*.svg')
            # all_img = list(getOrderedList(self.img_dir+'/*.svg'))
            all_img = list(getFiles(self.img_dir, ext='.svg', index=self.index))
            if img_name in all_img:
                all_img.remove(img_name)
            img_name = random.choice(all_img)
            layers = getLayerNames(img_name)
        elif fake_img:
            assert img_name is None
            assert not ran_img
            layers = self.getFakeLayers()
        else:
            layers = getLayerNames(img_name)

        assert(layers in self.all_layers), ('layer not identified!', layers)

        return layers, sent

    # def encode(self, layers=None, sent=None, **kwargs):
    def encode(self, layers=None, sent=None):

        # tofeature
        txt_embed = self.txt_encoder.encode(sent)
        img_embed = self.img_encoder.encode(layers)
        joint_embed = self.joint_encoder.encode(layers, sent)

        # return joint_embed

        return np.hstack([txt_embed, img_embed, joint_embed])

    def __getitem__(self, ind):
        img_name = '%s/%i.svg' % (self.img_dir, ind+1)
        txt_name = '%s/%i.txt' % (self.txt_dir, ind+1)

        # assert((layers and sent) or (not layers and not sent)), 'layers and sentence must be provided together, or neither'

        # get layers
        # if not layers and not sent:
        #     layers, sent = self.getOneLayerSent(**kwargs)

        # triplets
        triplets = []
        triplets_pair = []

        # true match
        layers, sent = self.getOneLayerSent(txt_name=txt_name,
                                            img_name=img_name)
        triplets_pair.append((layers, sent))
        triplets.append(self.encode(layers, sent))

#         # fake image
#         triplets.append(self.encode(txt_name=txt_name,
#                                     fake_img=True))
        # mismatched text
        layers, sent = self.getOneLayerSent(txt_name=txt_name,
                                            img_name=img_name,
                                            ran_txt=True)
        triplets_pair.append((layers, sent))
        triplets.append(self.encode(layers, sent))

        # mismatched image
        layers, sent = self.getOneLayerSent(txt_name=txt_name,
                                            img_name=img_name,
                                            ran_img=True)
        triplets_pair.append((layers, sent))
        triplets.append(self.encode(layers, sent))

        xs = np.vstack(triplets)

        # ys
        # ys = np.array([1,0,0,0]).reshape(-1,1)
        ys = np.array([1,0,0]).reshape(-1,1)

        return sparse.csr_matrix(np.hstack([xs, ys])), triplets_pair

    def getFakeLayers(self):
        return ranGenLayer()

    def __len__(self):
        # return len(glob.glob(self.img_dir+'/*.svg'))
        # return len(list(getOrderedList(self.img_dir+'/*.svg')))
        return len(list(getFiles(self.img_dir, ext='.svg', index=self.index)))


class DatasetReality(Dataset):
    """
    Dataset used to discriminate real images and fake images
    """
    def __init__(self, img_dir='images', txt_dir='text', index=None, **kwargs):

        super().__init__(img_dir, txt_dir, index, **kwargs)

        # all layers that appeared
        # all_imgs = glob.glob(self.img_dir+'/*.svg')
        print(' - Build fake layers..')
        # all_imgs = list(getOrderedList(self.img_dir+'/*.svg'))
        all_imgs = list(getFiles(self.img_dir, ext='.svg', index=self.index))
        self.true_layers = [getLayerNames(img) for img in all_imgs]
        self.fake_layers = self.__list_diff(self.all_layers,
                                            self.true_layers)

        print(' - Set feature names..')
        # features
        self.features_ = self.img_encoder.features_

    def __list_diff(self, all_, true):
        true = set([tuple(l) for l in true])
        all_ = set([tuple(l) for l in all_])
        # sort to ensure reproduction
        fake = sorted([list(l) for l in all_ - true])
        assert(len(fake) == len(all_) - len(true))
        return fake

    def __getitem__(self, ind):
        img_name = '%s/%i.svg' % (self.img_dir, ind+1)

        # pairs
        pairs = []
        layer_pairs = []

        # true image
        layers = getLayerNames(img_name)
        layer_pairs.append(tuple(layers))
        pairs.append(self.img_encoder.encode(layers))

        # fake image
        fake_layers = self.getFakeLayers()
        layer_pairs.append(tuple(fake_layers))
        pairs.append(self.img_encoder.encode(fake_layers))

        xs = np.vstack(pairs)

        # ys
        ys = np.array([1,0]).reshape(-1,1)

        return sparse.csr_matrix(np.hstack([xs, ys])), layer_pairs

    def getFakeLayers(self):
        """
        rewrite the fake generation
            choose from layers not appeared
        """
        ## todo - this could be the same as the contrast layer, though rare
        return random.choice(self.fake_layers)
