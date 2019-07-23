#!./env python
import numpy as np
import glob
import random
from scipy import sparse

from tools.text_process import LemmaTokenizer
from tools.image_process import getLayerNames, checkLayerNames, image2feature
from models.vectorizer import getVectorizer

# Similarity between category keywords and the description
# suppress cats not in image??**
from tools.image_process import image2SimiFeature

# random image generator, subject to rules
from tools.generator import ranGenLayer

class Dataset():
    """
    **Deprecated**
    use max sentence Similarity as feature --> not intepretable
    """
    def __init__(self, img_dir='images', txt_dir='text'):
        self.img_dir = img_dir
        self.txt_dir = txt_dir
        self.tokenizer = LemmaTokenizer()
        # this operation will process all the text and train a vectorizer
        # so we have double processed the text here
        self.vectorizer = getVectorizer()

        # set features
        self.__get_featureNames()

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
            orig_sent = f.read()
            sent = self.tokenizer(orig_sent)

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
            layers = ranGenLayer()
        else:
            layers = getLayerNames(img_name)

        return layers, sent

    def __getEmbed(self, **kwargs):

        layers, sent = self.getOneLayerSent(**kwargs)

        # tofeature
        txt_embed = self.vectorizer.transform([sent]).toarray()[0]
        img_embed = image2feature(layers)
        joint_embed = image2SimiFeature(layers, sent)

        return np.hstack([txt_embed, img_embed, joint_embed])

    def __getitem__(self, ind):
        img_name = '%s/%i.svg' % (self.img_dir, ind+1)
        txt_name = '%s/%i.txt' % (self.txt_dir, ind+1)

        # triplets
        triplets = []
        # true match
        triplets.append(self.__getEmbed(txt_name=txt_name,
                                        img_name=img_name))
        # fake image
        triplets.append(self.__getEmbed(txt_name=txt_name,
                                        fake_img=True))
        # mismatched text
        triplets.append(self.__getEmbed(img_name=img_name,
                                        txt_name=txt_name,
                                        ran_txt=True))
        # mismatched image
        triplets.append(self.__getEmbed(img_name=img_name,
                                        txt_name=txt_name,
                                        ran_img=True))

        xs = np.vstack(triplets)

        # ys
        ys = np.array([1,0,0,0]).reshape(-1,1)

        return sparse.csr_matrix(np.hstack([xs, ys]))


    def __len__(self):
        return len(glob.glob(self.img_dir+'/*.svg'))

    def __get_featureNames(self):
        self.features_ = []
        # text features
        self.vocab_, _ = zip(*sorted(self.vectorizer.vocabulary_.items(),
                                     key=lambda x:x[::-1]))
        self.features_.extend(list(self.vocab_))

        # image features
        from tools.image_process import getNestedKey
        from rules.category import surrouding_dict, person_dict
        self.features_.append('_NLayers_')
        self.features_.extend(['_Background_',
                               '_Surroundings_',
                               '_Person_',
                               '_Decoration_'])
        srd_keys = getNestedKey(surrouding_dict)
        prs_keys = getNestedKey(person_dict)
        self.features_.extend(['_S_%s_' % k for k in srd_keys])
        self.features_.extend(['_P_%s_' % k for k in prs_keys])

        # joint features
        self.features_.extend(['_simi_S_%s_' % k for k in srd_keys])
        self.features_.extend(['_simi_P_%s_' % k for k in prs_keys])
