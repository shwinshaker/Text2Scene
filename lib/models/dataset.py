#!./env python

import numpy as np
import random
from scipy import sparse

from .encoder import TextPictureRavelHistSimiEncoder
from ..tools.containers import LayerName, Picture, Description

class Dataset():
    def __init__(self, img_dir='../dataset/images',
                       txt_dir='../dataset/text',
                       names=[]):

        self.img_dir = img_dir
        self.txt_dir = txt_dir
        self.names = names # specify training data

        print(' - Initialize encoder..')
        self.encoder = TextPictureRavelHistSimiEncoder(names=names)
        self.features_ = self.encoder.features_

    def _get_pair(self, txt_name=None, img_name=None,
                        ran_txt=False, ran_img=False,
                        fake_img=False):
        ##### preprocess
        ## text
        assert txt_name
        doc = Description(txt_name)

        if ran_txt:
            # make sure random chosen doc are different
            while True:
                ran_doc = random.choice(list(self.encoder.textbase.doc_vocab_))
                if ran_doc != doc:
                    break
            doc = ran_doc
        else:
            # use true doc
            pass

        ## image
        assert img_name
        pic = Picture(img_name)

        if ran_img:
            # then choose one from all unique pictures
            assert not fake_img

            # make sure random chosen pic are different
            while True:
                ran_pic = random.choice(list(self.encoder.layerbase.pic_vocab_))
                if ran_pic != pic:
                    break
            pic = ran_pic

        elif fake_img:
            # then choose several unique layers
            assert not ran_img

            # make sure random chosen pic are different
            while True:
                # randomly choose 1 - 5 layers
                num_layers = random.choice(range(1,6))
                ran_layers = []
                for _ in range(num_layers):
                    ran_layers.append(random.choice(list(self.encoder.layerbase.layer_vocab_)))
                ran_pic = Picture(layernames=[l.s for l in ran_layers])
                if ran_pic != pic:
                    break
            pic = ran_pic
        else:
            # use true pic
            pass

        return doc, pic

    def encode(self, doc, pic):
        return self.encoder.encode(doc, pic)

    def __getitem__(self, name):
        img_name = '%s/%s.svg' % (self.img_dir, name)
        txt_name = '%s/%s.txt' % (self.txt_dir, name)

        # assert((layers and sent) or (not layers and not sent)), 'layers and sentence must be provided together, or neither'

        # get layers
        # if not layers and not sent:
        #     layers, sent = self.getOneLayerSent(**kwargs)

        # triplets
        triplets = []
        triplets_pair = []

        # true match
        doc, pic = self._get_pair(txt_name=txt_name,
                                  img_name=img_name)
        triplets_pair.append((doc, pic))
        # print('- encode true pairs..')
        triplets.append(self.encode(doc, pic))


        # mismatched text
        doc, pic = self._get_pair(txt_name=txt_name,
                                      img_name=img_name,
                                      ran_txt=True)
        triplets_pair.append((doc, pic))
        # print('- encode true pic and ran doc..')
        triplets.append(self.encode(doc, pic))

        # mismatched image
        doc, pic = self._get_pair(txt_name=txt_name,
                                      img_name=img_name,
                                      ran_img=True)
        triplets_pair.append((doc, pic))
        # print('- encode true doc and ran pic..')
        triplets.append(self.encode(doc, pic))

        # fake image
        # triplets.append(self.encode(txt_name=txt_name,
        #                             fake_img=True))

        # concatenate
        xs = np.vstack(triplets)
        ys = np.array([1,0,0]).reshape(-1,1)

        return sparse.csr_matrix(np.hstack([xs, ys])), triplets_pair

    def getFakeLayers(self):
        pass
        return ranGenLayer()

    def __len__(self):
        # return len(glob.glob(self.img_dir+'/*.svg'))
        # return len(list(getOrderedList(self.img_dir+'/*.svg')))
        # return len(list(getFiles(self.img_dir, ext='.svg', index=self.index)))
        return len(self.names)


