#!./env python

import random
# random.seed(7)
from tools.image_process import checkLayerNames
from rules.category import surrouding_dict, person_dict

### random generator
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


from tools.common import getAllKeyCombsFromNested, keyword2Code, packAppend
### exhaustive generator
def getAllHeadLayersCode():
    """
    Get all possible head code combinations
    Eg. [[0,1,0,0], [0,0,1,0], ...]
    """
    SP = [[s, p] for s in [1,0] for p in [1,0]]
    SP.remove([0,0]) # person or surrounding, must have one
    BD = [[b, d] for b in [1,0] for d in [1,0]]
    return [[bd[0]] + sp + [bd[1]] for sp in SP for bd in BD]

def expandCategory(layers_code):
    """
    Expand a layer code by all possible combinations of category subcodes
    """

    def _getAllSubcode(dic):
        """
        Get all possible subcodes of a nested dictionary
        """
        return [keyword2Code(dic, keys) for keys in getAllKeyCombsFromNested(dic)]

    def _code2Layer(head, codes):
        """
        Given head category's code and subcodes, output layer name
        Eg. 2, [1,1,1] -> 'A2111'
        """
        return 'A' + str(head) + ''.join([str(c) for c in codes])


    # get existing head codes based on the binary code
    head_codes = [i+1 for i,v in enumerate(layers_code) if v == 1]

    # get all subcodes combinations
    subcodes_srd = _getAllSubcode(surrouding_dict)
    subcodes_prs = _getAllSubcode(person_dict)

    # expand headcode based on possible subcodes
    if 1 in head_codes:
        # layers_0 = [['A1']]
        layers = [['A1']]
    else:
        # layers_0 = [[]]
        layers = [[]]

    """
    Let's resolve the occlusion tentatively. This feature seems not quite useful.
    """
    if 2 in head_codes:
        # layers = packAppend(layers_0, [_code2Layer(2, c) for c in subcodes_srd])
        layers = packAppend(layers, [_code2Layer(2, c) for c in subcodes_srd])

    if 3 in head_codes:
        layers = packAppend(layers, [_code2Layer(3, c) for c in subcodes_prs])

    # if 2 in head_codes:
    #     layers = packAppend(layers_0, [_code2Layer(2, c) for c in subcodes_srd])
    #     if 3 in head_codes:
    #         layers_23 = packAppend(layers, [_code2Layer(3, c) for c in subcodes_prs])
    #         # reverse the order
    #         layers_32 = packAppend(layers_0, [_code2Layer(3, c) for c in subcodes_prs])
    #         layers_32 = packAppend(layers_32, [_code2Layer(2, c) for c in subcodes_srd])
    #         layers = layers_23 + layers_32
    # else:
    #     assert 3 in head_codes
    #     layers = packAppend(layers_0, [_code2Layer(3, c) for c in subcodes_prs])

    if 4 in head_codes:
        layers = packAppend(layers, ['A4'])
    return layers

def getAllLayerCombs():
    """
    Get all possible layer combinations
    Eg. [['A1','A2111'],['A1','A311'],['A1','A2111','A311'],...]
    """
    all_layers = []
    for layers in getAllHeadLayersCode():
        all_layers.extend(expandCategory(layers))
    # sanity check
    assert(len(all_layers) == 11*4+13*4+11*13*4), len(all_layers)
    for layer in all_layers:
        checkLayerNames(layer)
    return all_layers
