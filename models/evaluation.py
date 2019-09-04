#!./env python

from models.metric import WeightedMeanIOU
from tools.containers import Picture, Description
from tools.common import getBase
import glob
import os

def avg_list_of_dict(ld):
    keys = ld[0].keys()
    avg_ = {}
    for key in keys:
        avg_[key] = sum([d[key] for d in ld]) / len(ld)
    return avg_

def score(generate, metric, dir_suffix='train', verbose=True):
    txt_dir = 'text_%s' % dir_suffix
    img_dir = 'images_%s' % dir_suffix
    assert(os.path.isdir(txt_dir)), txt_dir
    assert(os.path.isdir(img_dir)), img_dir

    simis = []
    for name in [getBase(path) for path in glob.glob('%s/*.txt' % txt_dir)]:
        desc = Description('%s/%s.txt' % (txt_dir, name))
        true_pic = Picture('%s/%s.svg' % (img_dir, name))
        gen_pic = generate(desc.text_)
        simi = metric.picture_simi(true_pic, gen_pic,with_bg=False)
        simis.append(simi)

        metric.save_dict()
        # generate.layerground.save_dict()
        # generate.keywordground.save_dict()

        print('\n ----------- %s ------------- ' % name)
        if verbose:
            print(str(desc).strip('\n'))
            print(true_pic)
            print(gen_pic)
            print(simi)

    return avg_list_of_dict(simis)

def pprint(train_simi_dict, test_simi_dict):
    print('        Overall    subj    act    obj')
    print('train:   %.2f     %.2f     %.2f    %.2f' % (train_simi_dict['overall'], train_simi_dict['subj'], train_simi_dict['act'], train_simi_dict['obj']))
    print('test:   %.2f     %.2f     %.2f    %.2f' % (test_simi_dict['overall'], test_simi_dict['subj'], test_simi_dict['act'], test_simi_dict['obj']))

def evaluate(generate, verbose=True):
    metric = WeightedMeanIOU()
    train_simi_dict = score(generate,
                            metric,
                            dir_suffix='train', verbose=verbose)
    test_simi_dict = score(generate,
                           metric,
                           dir_suffix='val', verbose=verbose)

    pprint(train_simi_dict, test_simi_dict)

    return train_simi_dict, test_simi_dict
