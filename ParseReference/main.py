import os
import sys
import json
import subprocess
from sklearn.cross_validation import KFold
from sklearn.metrics import precision_score, recall_score, f1_score

from data_preprocessor import n_un_data_split, data_split, reduction


def process_one_fold(fold_num,
                     clf_dir,
                     bsl_dir,
                     data_dir,
                     size_dir,
                     path_to_model,
                     data_gatherer,
                     acc_info):
    datafile = data_dir + size_dir + 'data_{0}.json'.format(fold_num)
    candsfile = data_dir + size_dir + 'cnds_{0}.json'.format(fold_num)
    resfile = data_dir + size_dir + 'res_{0}.json'.format(fold_num)

    bsltimefile = data_dir + size_dir + 'bsltime.json'
    clftimefile = data_dir + size_dir + 'clftime.json'

    train_data, test_data = data_gatherer()

    with open(datafile, 'w') as bsl_data:
        json.dump((train_data, test_data), bsl_data)

    training_proc = None
    if not os.path.exists(clf_dir + path_to_model) or \
            not filter(lambda f: f.endswith('{0}.model'.format(fold_num)),
                       os.listdir(clf_dir + path_to_model)):
        # Launch training process. No need to wait because BSL works independently
        training_proc = subprocess.Popen(['./run_clf.sh', clf_dir,
                                                          'train',
                                                          '../' + datafile,
                                                          'qqq',
                                                          path_to_model,
                                                          '../' + clftimefile,
                                                          'clf_train.log'])
    else:
        print '  Models are trained.'

    if not os.path.isfile(candsfile):
        # Launch BSL. Need to wait cands before finding schemas
        try:
            subprocess.check_call(['./get_cands.sh', bsl_dir,
                                                     '../' + datafile,
                                                     '../' + candsfile,
                                                     '../' + bsltimefile])
        except subprocess.CalledProcessError as e:
            print 'BSL-controller failed: code is {0}'.format(e.returncode)
    else:
        print '  Candidates are found.'

    if training_proc:
        # Wait for learning is complete
        ret_code = training_proc.wait()

    if not os.path.isfile(resfile):
        # Parse posts. Need to wait results to compute precision and recall
        try:
            subprocess.check_call(['./run_clf.sh', clf_dir,
                                                   'parse',
                                                   '../' + candsfile,
                                                   '../' + resfile,
                                                   path_to_model,
                                                   '../' + clftimefile,
                                                   'clf_parse.log'])
        except subprocess.CalledProcessError as e:
            print 'Parsing failed: code is {0}'.format(e.returncode)
    else:
        print '  Test posts are parsed.'

    if fold_num not in acc_info:
        # Accuracy for this fold is not computed - do it!
        acc_fold_info = {}

        # construct dict with indices for each metadata
        meta_inds = {}
        for sample in train_data:
            str_meta = meta_to_str(sample['attr'])
            if str_meta not in meta_inds:
                meta_inds[str_meta] = len(meta_inds)
        unknown_meta_num = 0
        for sample in test_data:
            str_meta = meta_to_str(sample['attr'])
            if str_meta not in meta_inds:
                # these metadata are not represented in reference set
                # schema finder always fail at this samples
                meta_inds[str_meta] = -1
                unknown_meta_num += 1

        note = 'In fold {0} test samples contains {1} unknown papers (from {2})'
        print note.format(fold_num, unknown_meta_num, len(test_data))
        acc_fold_info['unknown'] = (unknown_meta_num, len(test_data))

        # construct vector of true answers and the one of predictions
        with open(resfile, 'r') as input:
            parse_data = json.load(input)

        vect_true = []
        vect_pred = []
        for parse_res in parse_data:
            schema_res = parse_res[0]
            attrs_res = parse_res[1]

            ts = next((ts for ts in test_data
                       if ts['name'].replace('\\', '') == schema_res['post']))
            str_meta = meta_to_str(ts['attr'])
            vect_true.append(meta_inds[str_meta])

            str_schema = meta_to_str(schema_res['schema'])
            vect_pred.append(meta_inds[str_schema])

        # compute precision and recall
        acc_fold_info['precision'] = precision_score(vect_true,
                                                     vect_pred,
                                                     average='micro')
        acc_fold_info['recall'] = recall_score(vect_true,
                                               vect_pred,
                                               average='micro')
        acc_fold_info['f1'] = f1_score(vect_true,
                                       vect_pred,
                                       average='micro')

        print 'Schema finder accuracy (fold {0}):'.format(fold_num)
        print '    precision: {0}'.format(acc_fold_info['precision'])
        print '       recall: {0}'.format(acc_fold_info['recall'])
        print '           f1: {0}'.format(acc_fold_info['f1'])

        acc_info[fold_num] = acc_fold_info

    else:
        print '  Accuracy info is computed.'


def main(size):
    data_dir = 'data/'
    bsl_dir = 'BSL/'
    clf_dir = 'clf/'

    size_dir = 'size_{0}/'.format(size)
    if not os.path.exists(data_dir + size_dir):
        os.makedirs(data_dir + size_dir)

    # All data about accuracy is here
    accfile = data_dir + size_dir + 'accuracy.json'
    if os.path.isfile(accfile):
        with open(accfile, 'r') as input:
            acc_info = json.load(input)
    else:
        acc_info = {}

    path_to_model = 'data/' + size_dir

    raw_samples = data_dir + 'raw_samples.json'
    samples = data_dir + 'samples.json'
    keys = ('author', 'title', 'journal', 'year', 'pages')
    split_samples = data_dir + 'split_samples.json'
    n_un_split_samples = data_dir + 'n_un_split_samples.json'
    n_folds = cv_n_folds = 10

    reduction(raw_samples, samples, keys)
    data_split(samples, split_samples, n_folds, size=size)
    n_un_data_split(samples, n_un_split_samples, size=size)

    # Compute non-unknown test cases
    fold_num = 'n_un'
    print 'Processing fold \'{0}\'.'.format(fold_num)

    process_one_fold(fold_num,
                     clf_dir,
                     bsl_dir,
                     data_dir,
                     size_dir,
                     path_to_model,
                     lambda: n_un_data_gatherer(n_un_split_samples),
                     acc_info)

    # Compute cross-validation
    kf = KFold(n_folds, n_folds=cv_n_folds)

    fold_num = 0
    for train_ind, test_ind in kf:
        fold_num += 1
        print 'Processing fold {0}.'.format(fold_num)

        process_one_fold(fold_num,
                         clf_dir,
                         bsl_dir,
                         data_dir,
                         size_dir,
                         path_to_model,
                         lambda: fp_data_gatherer(train_ind, test_ind, split_samples),
                         acc_info)

        # Comment 'break' for cross-validation
        # break

    with open(accfile, 'w') as output:
        json.dump(acc_info, output)

    print 'Yo-ho-ho, motherfucker!!!'


def fp_data_gatherer(train_ind, test_ind, datafile):
    with open(datafile, 'r') as input:
        data = json.load(input)

    train_data = []
    test_data = []
    for ind in train_ind:
        train_data.extend(data[ind])
    for ind in test_ind:
        test_data.extend(data[ind])

    return train_data, test_data


def n_un_data_gatherer(datafile):
    with open(datafile, 'r') as input:
        data = json.load(input)

    return data


def meta_to_str(meta):
    return str(sorted(meta.items(), key=lambda x: x[0]))


if __name__ == "__main__":
    size = int(sys.argv[1])
    main(size)
