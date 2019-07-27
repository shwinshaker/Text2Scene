#!./env python

def exhaustiveSearch(query_txt, lamb=0.7):
    print('text: %s' % query_txt)
    print('tokens:', dataset.txt_encoder.tokenizer(query_txt))
    probs = []
    for i, layers in enumerate(dataset.all_layers):
        print('[%i]' % i, end='\r')
        X = dataset.encode(sent=query_txt, layers=layers)
        prob_consis = np.squeeze(clf.predict_proba(X.reshape(1,-1)))[1]
        X_r = dataset_r.img_encoder.encode(layers)
        prob_real = np.squeeze(clf_r.predict_proba(X_r.reshape(1,-1)))[1]
        probs.append((i, prob_consis*lamb + prob_real*(1-lamb)))

    imax, max_prob = max(probs, key=lambda x: x[1])
    max_layers = dataset.all_layers[imax]
    print('Most consistent layer:', max_layers, 'Prob: %.6f' % max_prob)
    print('Corresponding keywords:', dataset.img_encoder.layer2keyword(max_layers))
    return max_layers
