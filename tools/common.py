#!./env python

## Nested list
def flattenNested(nested):
    """
    Flatten a nested list
        support two-level nested, with number mixed
        Eg. [3,[1,2,3],5,[2,4]]
    """
    flatten = []
    for l in nested:
        if isinstance(l, list):
            assert(isPureList(l))
            flatten.extend([e for e in l])
        else:
            flatten.append(l)
    return flatten

def getDepth(li):
    """
    Get the depth of a nested list
    """
    for level in count():
        if not li:
            return level
        li = [e for l in li if isinstance(l, list) for e in l]

def recurReplace(nested, id_list, value=1):
    """
    Replace an element in a nested list recursively
    """
    # number of indexes should be lower than the depth
    assert(len(id_list) <= getDepth(nested))

    # print(nested, '--', id_list)
    if len(id_list) > 1:
        recurReplace(nested[id_list[0]], id_list[1:])
    else:
        nested[id_list[0]] = value

def isPureList(l):
    """
    Check if a list is not a nested one
    """
    for e in l:
        if isinstance(e, list):
            return False
    return True

def code2indslist(code):
    """
    Turn a code into the reference indexes of a nested list
        Eg. [2,1,2,1] -> [0,1,0]
        the first number is the ident code of the layer type
    """
    return [d-1 for d in code[1:]]

def extractLeaf(feat, depth, concat=[], level=0):
    """
    Extract the leaf lists in the same level in a nested list
    """
    level += 1
    # print('  ', level, depth, concat)
    for i, e in enumerate(feat):
        if isinstance(e, list):
            if isPureList(e):
                # lowest level only
                if level == depth - 1:
                    concat.extend(e)
                    feat[i] = sum(e)
            else:
                feat[i], concat = extractLeaf(e, depth, concat, level)
    return feat, concat


## Nested dictionary

def getNestedKey(obj):
    """
    recursion wrapper of getNestedKey_
    """
    keys = []
    getNestedKey_(obj, keys=keys)
    return keys

def getNestedKey_(obj, keys=[]):
    """
    get all the keys in a nested dictionary
        todo - keys argument can be saved if use reference
    """
    if isinstance(obj, dict):
        for key in obj:
            keys.append(key)
            getNestedKey_(obj[key], keys)
    elif isinstance(obj, list):
        for key in obj:
            getNestedKey_(key, keys)
    elif isinstance(obj, str):
        keys.append(obj)
    else:
        raise KeyError

def getNestedKeyWithCode(obj, code):
    """
    get the correspondings keywords to the code in a nested dictionary
    """
    keys = []
    for c in code:
        if isinstance(obj, dict):
            key = list(obj.keys())[c - 1]
            keys.append(key)
            obj = obj[key]
        elif isinstance(obj, list):
            l = []
            for key in obj:
                if isinstance(key, str):
                    l.append(key)
                elif isinstance(key, dict):
                    l.extend(list(key.keys()))
                else:
                    raise TypeError('Invalid type other than str and dict')
            key = l[c - 1]
            keys.append(key)
            if key in obj:
                obj = key # should end here
            else:
                for obj_ in obj:
                    if isinstance(obj_, dict) and key in obj_.keys():
                        obj = obj_[key]
        else:
            raise TypeError('Invalid type other than str and dict. Could be incorrect query code!')
    return keys
