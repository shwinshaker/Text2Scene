#!./env python

import random
from tools.image_process import checkLayerNames
from rules.category import surrouding_dict, person_dict

def ranGenCatCode():
    """
    Randomly generate a set of legal category codes
    """
    while True:
        try:
            binary = [random.randint(0, 1) for _ in range(4)]
            # print(binary)
            cat_code = [i+1 for i in range(len(binary)) if binary[i] == 1]
            assert(cat_code)

            # random shuffle the overlapping order
            random.shuffle(cat_code)
            # print(cat_code)

            # check if layer names are legal
            checkLayerNames(cat_code)
            break
        except AssertionError:
            pass
    return cat_code

def ranAssignNested(obj, code=[]):
    """
    Randomly assign an element into a category tree
    """
    if isinstance(obj, dict):
        keys = list(obj.keys())
        key = random.choice(keys)
        code.append(keys.index(key) + 1)
        code = ranAssignNested(obj[key], code)
    elif isinstance(obj, list):
        keys = []
        for key in obj:
            if isinstance(key, str):
                keys.append(key)
            elif isinstance(key, dict):
                keys.extend(list(key.keys()))
            else:
                raise TypeError('Invalid type other than str and dict')
        key = random.choice(keys)
        ind = keys.index(key)
        code.append(ind + 1)
        if key in obj:
            # string, end
            return code
        else:
            for obj_ in obj:
                if isinstance(obj_, dict) and key in obj_.keys():
                    code = ranAssignNested(obj_[key], code)
    else:
        raise KeyError
    return code

def ranGenLayer():
    cat_code = ranGenCatCode()
    layers = []
    for c in cat_code:
        if c == 1:
            layers.append('A1')
        elif c == 4:
            layers.append('A4')
        elif c == 2:
            code = ranAssignNested(surrouding_dict, code=[])
            code = [str(c) for c in code]
            layers.append('A2'+''.join(code))
        elif c == 3:
            code = ranAssignNested(person_dict, code=[])
            code = [str(c) for c in code]
            layers.append('A3'+''.join(code))
        else:
            raise KeyError('Invalid code %i!' % c )
    return layers
