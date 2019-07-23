#!./env python

def getVectorizer():
    # text reader
    import glob
    from tools.text_process import LemmaTokenizer
    tokenizer = LemmaTokenizer()
    sentences = []
    for fileName in sorted(glob.glob('text/*.txt')):
        with open(fileName, 'r') as f:
            sent = f.read()
            tokens = tokenizer(sent)
            sentences.append(tokens)

    ## vectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

    vectorizer = TfidfVectorizer(ngram_range=(1,2),
                                 norm=None,
                                 sublinear_tf=True,
                                 stop_words=[],
                                 lowercase=False,
                                 tokenizer=lambda l: l)
    vectorizer.fit(sentences)

    return vectorizer
