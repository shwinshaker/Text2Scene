#!./env python

import requests
import time
import dill
from json.decoder import JSONDecodeError
from tools.common import ravel, static_vars
from tools.knowledge import LayerBase, TextBase

@static_vars(count_query=0, count_stored=0)
def query(token, layerbase, relateDict):
    """
    Caveats: conceptNet doesn't differ pos in relatedness
    """

    for keyword in layerbase.keywords_:
        # seen
        ## relatedness does not differ different pos
        if keyword.t in relateDict and token.t in relateDict[keyword.t]:
            query.count_stored += 1
            print(' stored [%i] ' % query.count_stored, end='\r')
            continue

        # unseen. query conceptNet
        query.count_query += 1
        print('Query: %i %s - %s' % (query.count_query, keyword.t, token.t))
        while True:
            try:
                s = requests.get('http://api.conceptnet.io/relatedness?node1=/c/en/%s&node2=/c/en/%s' % (keyword.t, token.t)).json()['value']
            except JSONDecodeError:
                print('Buffered! Wait for 10 secs')
                for i in range(10):
                    print('- %i' % (i+1), end='\r')
                    time.sleep(1)
                print('- try now')
                continue
            break
        relateDict[keyword.t][token.t] = s

def loop_query(textbase, layerbase, relateDict):

    for token in textbase.vocab_:
        query(token, layerbase, relateDict)
        with open('relateDict.pkl', 'wb') as f:
            dill.dump(relateDict, f)

def main():
    with open('relateDict.pkl', 'rb') as f:
        relateDict = dill.load(f)

    layerbase = LayerBase()
    textbase = TextBase()
    loop_query(textbase, layerbase, relateDict)

if __name__ == '__main__':
    main()
