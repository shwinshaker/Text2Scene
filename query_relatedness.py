#!./env python

import requests
import time
# import dill
import pickle
from json.decoder import JSONDecodeError
from tools.common import ravel, static_vars
from tools.knowledge import LayerBase, TextBase

def mirror():
    """
    sometimes need to mirror the relatedDict
        no need now since every query save both sides
    """
    with open('relateDict.pkl', 'rb') as f:
        relateDict = pickle.load(f)

    from tools.common import ddict2dict
    mirror_dict = defaultdict(lambda: defaultdict(float))
    for k1 in relateDict:
        for k2 in relateDict[k1]:
            mirror_dict[k1][k2] = relateDict[k1][k2]
            mirror_dict[k2][k1] = relateDict[k1][k2]

    relateDict = ddict2dict(mirror_dict)
    with open('relateDict.pkl', 'wb') as f:
        pickle.dump(relateDict, f)

def wait(secs=10):
    for i in range(10):
        print('- %i' % (i+1), end='\r')
        time.sleep(1)

@static_vars(count_query=0)
# def query(token, layerbase, relateDict):
def query_simi(token, keyword):
    """
    Caveats: conceptNet doesn't differ pos in relatedness
    """
    with open('relateDict.pkl', 'rb') as f:
        # relateDict = dill.load(f)
        relateDict = pickle.load(f)

    if token in relateDict and keyword in relateDict[token]:
        return relateDict[token][keyword]

    # recur query
    while True:
        try:
            query_simi.count_query += 1
            print('Query Request: %i %s - %s' % (query_simi.count_query, keyword, token))
            s = requests.get('http://api.conceptnet.io/relatedness?node1=/c/en/%s&node2=/c/en/%s' % (keyword, token)).json()['value']
        except JSONDecodeError:
            print('Buffered! Wait for 10 secs')
            wait(10)
            print('- try now')
            continue
        break

    if keyword not in relateDict:
        relateDict[keyword] = {}
    if token not in relateDict:
        relateDict[token] = {}
    relateDict[keyword][token] = s
    relateDict[token][keyword] = s
    with open('relateDict.pkl', 'wb') as f:
        pickle.dump(relateDict, f)

    return s

def loop_query(textbase, layerbase):

    with open('relateDict.pkl', 'rb') as f:
        relateDict = pickle.load(f)

    count_stored = 0
    for token in textbase.vocab_:
        # for keyword in layerbase.keywords_:
        for keyword in layerbase.vocab_:
            # seen
            ## relatedness does not differ different pos
            if keyword.t in relateDict and token.t in relateDict[keyword.t]:
                count_stored += 1
                print(' stored [%i] ' % count_stored, end='\r')
                continue

            # unseen
            query_simi(token.t, keyword.t)
            # with open('relateDict.pkl', 'wb') as f:
            #     dill.dump(relateDict, f)

def main():

    print('Initialize layerbase..')
    layerbase = LayerBase()
    print('Initialize textbase..')
    textbase = TextBase()
    print('Loop query..')
    loop_query(textbase, layerbase)

if __name__ == '__main__':
    main()
