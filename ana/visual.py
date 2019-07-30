#!./env python
import matplotlib.pyplot as plt
import numpy as np

def _precision(true, pred):
    return sum(np.logical_and(pred == true, true)) / sum(pred)

def _recall(true, pred):
    return sum(np.logical_and(pred == true, true)) / sum(true)

def _acc(true, pred):
    return (sum(true == pred) / len(true))

def _F1(prec, recall):
    return 2 * prec * recall / (prec + recall)

def STAT(y_true, y_prob, path='STAT'):

    y_pred = y_prob > 0.5

    print('%i positives out of %i test examples' % (sum(y_true), len(y_true)))
    acc = _acc(y_true, y_pred) # (sum(y_true == y_pred) / len(y_true))
    recall = _recall(y_true, y_pred)
     # sum(np.logical_and(y_pred == y_true, y_true)) / sum(y_true)
    precision = _precision(y_true, y_pred)
     # sum(np.logical_and(y_pred == y_true, y_true)) / sum(y_pred)
    acc0 = _acc(1-y_true, 1-y_pred)
     # sum(np.logical_and(y_pred == y_true, 1-y_true)) / sum(1-y_true)
    print('Overall accuracy: %.6f' % acc)
    print('*Recall(thresh=0.5)/AccuracyOf1: %.6f' % recall)
    print('Precision(thresh=0.5): %.6f' % precision)
    print('AccuracyOf0(thresh=0.5): %.6f' % acc0)

    plt.figure()
    plt.hist(y_prob, #clf.predict_proba(X)[:,1],
             color='b',
             alpha=0.2,
             edgecolor='b')
    plt.hist(y_true, alpha=0.2, edgecolor='g')
    ylim = plt.gca().get_ylim()
    plt.plot([0.5,0.5], [ylim[0]+1, ylim[1]-1],'k--')
    plt.text(0.52, ylim[1]-2, 'Acc(1)=%.3f' % recall)
    plt.text(0.52, ylim[1]-3, 'Acc(0)=%.3f' % acc0)
    plt.text(0.52, ylim[1]-4, 'Acc(all)=%.3f' % acc)
    plt.xlabel('Predict probs')
    plt.ylabel('Counts')
    plt.xlim([0, 1])
    plt.savefig('results/%s' % path)
    # plt.show()

def ROC(y_true, y_prob, path='ROC'):
    from sklearn.metrics import precision_recall_curve
    from sklearn.metrics import average_precision_score
    from sklearn.metrics import roc_curve, auc
    from inspect import signature

    plt.figure(figsize=(10,4))
    # precision-recall curve
    plt.subplot(1,2,1)
    precision, recall, thresholds = precision_recall_curve(y_true,
                                                           y_prob)

    F1 = [_F1(p, r) for p, r in zip(precision, recall)]
    print('precision | recall | F1 | threshold')
    print('------------------------------')
    for p, r, f1, t in zip(precision, recall, F1, thresholds):
        print('%.3f | %.3f | %.3f | %.3f' % (p, r, f1, t))
    print('------------------------------')
    max_f1_tup = max(zip(precision, recall, F1, thresholds),
                     key=lambda x: x[2])

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
    plt.plot(max_f1_tup[1], max_f1_tup[0],
             marker='.', markersize=20, color='orange',
             label='mF1: %.2f - th: %.2f' % (max_f1_tup[2],
                                             max_f1_tup[3]))

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

    plt.savefig('results/%s' % path)
    # plt.show()


def FEAT(dataset, clf, path='FEAT'):
    d = dict(zip(dataset.features_, clf.coef_.tolist()[0]))
    d_filter = filter(lambda x: x[1] != 0, d.items())
    feat, valv = zip(*sorted(d_filter, key=lambda x: abs(x[1])))
    plt.figure(figsize=(4, round(len(feat)*0.25+2)))
    plt.barh(feat, valv)
    plt.savefig('results/%s' % path, bbox_inches='tight')
    # plt.show()
