#!./env python
from scipy import sparse
import glob
import re
import random
import pickle

### Nested list
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

def getDepth__(li):
    """
    Get the depth of a nested list
        *Deprecated*
    """
    from itertools import count
    for level in count():
        if not li:
            return level
        li = [e for l in li if isinstance(l, list) for e in l]

def getDepth(li):
    """
    Get the depth of a nested list
    Eg. depth([]) = 1
        depth([[]]) = 2
        depth([['']]) = 2
        depth([[''],'']) = 2
        depth([[''],['']]) = 2
    """
    # such that depth of [] = 1
    if len(li) == 0:
        li = ['']
    from itertools import count
    for level in count():
        if not li:
            return level
        # such that depth of [[]]=2, [[], '']=2, [[[]]]=3, etc.
        li = [[''] if isinstance(l, list) and len(l) == 0 else l for l in li]
        li = [e for l in li if isinstance(l, list) for e in l]

def getNodesWithDepth(li, depth):
    from itertools import count
    d0 = getDepth(li)
    assert(depth > 0), 'Depth starts from 1'
    assert(depth <= d0), 'Depth exceeds maximum depth %i' % d0
    for level in count():
        if level == depth:
            return nodes
        nodes = [l for l in li if not isinstance(l, list)]
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

def packInsert(key, l):
    """
    Insert a key to the head of all elements in a nested list
    Eg. 'a' [['b'],['c'],['d']] -> [['a','b'], ['a','c'], ['a', 'd']]
    """
    assert getDepth(l) == 2, l
    cl = []
    for k in l:
        cl.append([key] + k)
    return cl

def packAppend(l, append_l):
    """
    Append each one in a list of keys to each element in a nested list
    Eg. packAppend([['a'],['b'],['c']],['d','f'])
        return [['a', 'd'], ['a', 'f'], ['b', 'd'], ['b', 'f'], ['c', 'd'], ['c', 'f']]
    """
    assert getDepth(l) == 2, l
    assert getDepth(append_l) == 1, append_l
    new_l = []
    for k in l:
        for ka in append_l:
            new_l.append(k + [ka])
    return new_l


### Nested dictionary

def ddict2dict(d):
    """
    turn a nested defaultdict into dict
        such that unseen key will return keyError
    """
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = ddict2dict(v)
    return dict(d)

def dic2ddict(d):
    pass

def absorbNestedDict(dic1, dic2):
    """
    Input dictionary should be nested dictionary with set as leaf
        2.0
    """
    assert(isinstance(dic1, dict) or isinstance(dic1, set)), type(dic1)
    assert(isinstance(dic2, dict) or isinstance(dic2, set)), type(dic2)

    def __incre_key(dic, key):
        if isinstance(dic, dict):
            l_keys = list(dic.keys())
        elif isinstance(dic, set):
            l_keys = list(dic)
        else:
            raise TypeError
        k = l_keys[l_keys.index(key)]
        k.count += key.count

    for key in dic2:
        if key not in dic1:
            if isinstance(dic1, dict):
                dic1[key] = dic2[key]
            elif isinstance(dic1, set):
                # dic1.append(key)
                dic1.add(key)
            else:
                raise TypeError(dic1)
        else:
            if isinstance(dic1, dict):
                # absorbNestedDict(dic1[key], dic2[key])
                __incre_key(dic1, key)
                absorbNestedDict(dic1[key], dic2[key])
            elif isinstance(dic1, set):
                __incre_key(dic1, key)
            else:
                raise TypeError(dic1)

def ravel(entities_):
    """
    ravel a dict of dict to a node, with leaf as int
    """
    from tools.instance import Node

    assert(isinstance(entities_, dict))
    type0 = list(entities_.keys())[0]
    assert(isinstance(entities_[type0], dict))
    key0 = list(entities_[type0].keys())[0]
    assert(isinstance(entities_[type0][key0], int))

    ravel_ = set()
    for type_ in entities_:
        for key in entities_[type_]:
            node = Node(key, type_, count=entities_[type_][key])
            assert(node not in ravel_)
            ravel_.add(node)
    return ravel_

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

def code2Keyword(obj, code):
    """
    Another name
    """
    return getNestedKeyWithCode(obj, code)

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

def keyword2Code(obj, keys):
    """
    get the correspondings codes to the keywords in a nested dictionary
    """

    code = []
    for k in keys:
        if isinstance(obj, dict):
            code.append(list(obj.keys()).index(k) + 1)
            obj = obj[k]
        elif isinstance(obj, list):
            l = []
            for key in obj:
                if isinstance(key, str):
                    l.append(key)
                elif isinstance(key, dict):
                    l.extend(list(key.keys()))
                else:
                    raise TypeError('Invalid type other than str and dict')
            code.append(l.index(k) + 1)
            if k in obj:
                obj = k # should end here
            else:
                for obj_ in obj:
                    if isinstance(obj_, dict) and k in obj_.keys():
                        obj = obj_[k]
        else:
            raise TypeError('Invalid type other than str and dict. Could be incorrect query code!')
    return code

def getAllKeyCombsFromNested(obj):
    """
    Get all possible key combinations from a nested dictionary
    Eg. {'a':['b','c']} -> [['a','b'],['a','c']]
    """
    if isinstance(obj, dict):
        keys = []
        for key in obj:
            # keys.append([key])
            # codes.append([c+1 for c in range(len(obj))])
            keys.extend(packInsert(key, getAllKeyCombsFromNested(obj[key])))
    elif isinstance(obj, list):
        keys = []
        for key in obj:
            if isinstance(key, dict):
                assert(len(key) == 1), 'Only roots allowed in a list'
            childKeys = getAllKeyCombsFromNested(key)
            if getDepth(childKeys) == 1:
                keys.append(childKeys)
            else:
                keys.extend(childKeys)
    elif isinstance(obj, str):
        keys = [obj]
    else:
        raise TypeError('Invalid type other than str and dict. Could be incorrect query code!')

    return keys

def nestedDict2NestedList(obj):
    """
    convert a nested dictionary to a nested list
    """
    keys=[]
    if isinstance(obj, dict):
        for key in obj:
            keys.append(key)
            keys.append(nestedDict2NestedList(obj[key]))
    elif isinstance(obj, list):
        for key in obj:
            keys.extend(nestedDict2NestedList(key))
    elif isinstance(obj, str):
        keys.append(obj)
    else:
        raise KeyError
    return keys


# file IO

def getBase(path):
    """
    get the URI of a material
        E.g. images/play_day.svg -> play_day
    """
    assert(path.endswith('.txt') or path.endswith('.svg'))
    name = re.findall(r'.*/(\w+).\w+$', path)
    assert(len(name) == 1)
    return name[0]

def getFiles(path, ext, index=None):
    assert(ext.startswith('.')), 'extension must start with .!'

    if index is None:
        index = []
        for filename in glob.glob('%s/*%s' % (path, ext)):
            index.append(int(re.findall(r'\d+', filename)[0]))
        index.sort()

    for ind in index:
        yield '%s/%i%s' % (path, ind, ext)

    # for f in sorted(glob.glob('%s/*%s' % (path, ext)),
    #                 key=lambda f: int(re.findall(r'\d+', f)[0])):
    #     yield f

def getMaterial(layer):
    l = glob.glob('material/%s*.png' % layer)
    return random.choice(l)

# decorators
def static_vars(**kwargs):
    """
    Decoator to help function define static variables
        E.g. add a static counter: @static_vars(count=0)
    """
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

import time
def wait(secs=10):
    for i in range(secs):
        print('- %i' % (i+1), end='\r')
        time.sleep(1)

from json.decoder import JSONDecodeError
import requests
import atexit
from threading import Event
import sys
def enableQuery(cls):
    """
    decorator to add a similarty query function to the class
    """
    orig_init = cls.__init__

    def __init__(self, *args, **kws):
        """
        Caveats! Create two instances will cause two dicts opened!
            This is not a big problem.
        """
        orig_init(self, *args, **kws)
        self.exit = False # Event()
        self.exited = True
        self.dict_path = '%s/relateDict.pkl' % self.dict_dir
        with open(self.dict_path, 'rb') as f:
            relateDict = pickle.load(f)
        self.relateDict = relateDict
        """
        Caveats! only the first instance opened the dict can save the result at last.
            -> atexit registed functions are stacked.
            Because the each instance modifies the dict separately
                There's no way they can inform each other
        """
        atexit.register(self.save_dict)

    @static_vars(count_query=0)
    def query_simi(self, token, keyword):
        assert(isinstance(token, str)), token
        assert(isinstance(keyword, str)), (type(keyword), keyword)

        if token in self.relateDict and keyword in self.relateDict[token]:
            return self.relateDict[token][keyword]

        # if self.exit.is_set():
        if self.exit:
            print('>>>>>>>>>>> exit!')
            self.exited = True
            # raise RuntimeError('exit!')
            sys.exit(1)

        # recur query
        while True:
            try:
                query_simi.count_query += 1
                print('Query Request (%s): %i %s - %s' % (type(self).__name__, query_simi.count_query, keyword, token))
                s = requests.get('http://api.conceptnet.io/relatedness?node1=/c/en/%s&node2=/c/en/%s' % (keyword, token)).json()['value']
            except JSONDecodeError:
                print('Buffered! Wait for 10 secs')
                wait(10)
                print('- try now')
                continue
            break

        # save query results
        if keyword not in self.relateDict:
            self.relateDict[keyword] = {}
        if token not in self.relateDict:
            self.relateDict[token] = {}
        self.relateDict[keyword][token] = s
        self.relateDict[token][keyword] = s
        # if query_simi.count_query > 30:
        #     print(' saving dict...')
        #     with open(self.dict_path, 'wb') as f:
        #         pickle.dump(self.relateDict, f)
        #
        # if queried, save anyway
        with open(self.dict_path, 'wb') as f:
            pickle.dump(self.relateDict, f)
        return s

    def save_dict(self):
        print(' saving dict.. %s' % type(self).__name__)
        with open(self.dict_path, 'wb') as f:
            pickle.dump(self.relateDict, f)

    cls.__init__ = __init__
    cls.query_simi = query_simi
    cls.save_dict = save_dict

    return cls
