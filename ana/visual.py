#!./env python
import matplotlib.pyplot as plt
import numpy as np

def STAT(y_true, y_prob):

    y_pred = y_prob > 0.5

    print('%i positives out of %i test examples' % (sum(y_true), len(y_true)))
    print('Overall accuracy: %.6f' % (sum(y_true == y_pred) / len(y_true)))
    recall = sum(np.logical_and(y_pred == y_true, y_true)) / sum(y_true)
    precision = sum(np.logical_and(y_pred == y_true, y_true)) / sum(y_pred)
    acc0 = sum(np.logical_and(y_pred == y_true, 1-y_true)) / sum(1-y_true)
    print('*Recall(thresh=0.5)/AccuracyOf1: %.6f' % recall)
    print('Precision(thresh=0.5): %.6f' % precision)
    print('AccuracyOf0(thresh=0.5): %.6f' % acc0)

    plt.figure()
    plt.hist(y_prob, #clf.predict_proba(X)[:,1],
             color='b',
             alpha=0.2,
             edgecolor='b')
    plt.hist(y_true, alpha=0.2, edgecolor='g')
    plt.xlabel('Negative <-----                -----> Positive')
    plt.xlim([0, 1])
    plt.show()

def ROC(y_true, y_prob):
    from sklearn.metrics import precision_recall_curve
    from sklearn.metrics import average_precision_score
    from sklearn.metrics import roc_curve, auc
    from inspect import signature

    plt.figure(figsize=(10,4))
    # precision-recall curve
    plt.subplot(1,2,1)
    precision, recall, thresholds = precision_recall_curve(y_true,
                                                           y_prob)
    ap = average_precision_score(y_true, y_prob)
    # print(thresholds)
    # In matplotlib < 1.5, plt.fill_between does not have a 'step' argument
    step_kwargs = ({'step': 'post'}
                   if 'step' in signature(plt.fill_between).parameters
                   else {})
    plt.step(recall, precision, color='b', alpha=0.2,
             where='post')
    plt.fill_between(recall, precision, alpha=0.2,
                     color='b', **step_kwargs,
                     label='AP={0:0.2f}'.format(ap))

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title('Precision-Recall curve')
    plt.legend(loc="upper right")

    # ROC curve
    plt.subplot(1,2,2)
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    plt.plot(fpr, tpr, alpha=0.2,
             label='AUC = %0.2f' % auc(fpr, tpr))
    plt.fill_between(fpr, tpr, alpha=0.2, color='b')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title('Receiver operating characteristic')
    plt.legend(loc="upper left")

    plt.show()

def FEAT(dataset, clf):
    d = dict(zip(dataset.features_, clf.coef_.tolist()[0]))
    d_filter = filter(lambda x: x[1] != 0, d.items())
    feat, valv = zip(*sorted(d_filter, key=lambda x: abs(x[1])))
    plt.figure(figsize=(4, round(len(feat)*0.25+2)))
    plt.barh(feat, valv)
    plt.show()
