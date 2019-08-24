#!./env python

## export layers to dir named after file

import os

def export_layers(filenames=None):
    img_dir = 'images'
    if not filenames:
        filenames = sorted(os.listdir(img_dir))
    for file in filenames:
        base, ext = os.path.splitext(file)
        if ext == '.svg' and base != 'test' and base != 'stack':
            print(file)
            os.system("./export_svg.sh %s %s" % (file, img_dir))
            print(os.listdir('%s/m_%s' % (img_dir, base)))

def group_layers(prefix='m_', target='material', image_dir='images'):
    """
    Collect layers in separate dirs into material
    Extend name if necessary
    """
    import glob
    import shutil
    from tools.image_process import cleanName

    if os.path.exists(target):
        files = glob.glob(target+'/*')
        for file in files:
            os.remove(file)
    else:
        os.system('mkdir '+target)

    for d_ in sorted(os.listdir(image_dir)):
        d = image_dir + '/' + d_
        if os.path.isdir(d) and d_.startswith(prefix):
            print(d)
            for m in os.listdir(d):
                print('  %s' % m)
                if m in os.listdir(target):
                    base, ext = os.path.splitext(m)
                    base = cleanName(base)
                    num = len(glob.glob('%s/%s*.png' % (target,
                                                        base)))
                    new_m = '%s_(%s)%s' % (base, num, ext)
                else:
                    new_m = cleanName(m)
                shutil.copy(d+'/'+m, target+'/'+new_m)
            # os.rmdir(d)

if __name__ == '__main__':
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument(dest='filenames', metavar='Files', type=str, help='A query sentence')
    # filenames = ['virtual_reality.svg', 'voice_control.svg']
    # filenames = ['powerful.svg', 'problem_solving.svg', 'projections.svg']
    filenames = None
    export_layers(filenames)
    group_layers()
