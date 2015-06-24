import json


def construct_results_attrs(files):
    datadir = '../data/'

    result = {}
    for file in files:
        with open(datadir + file, 'r') as input:
            data = json.load(input)
        for record in data:
            result[record] = data[record]['attrs']

    return result


def construct_results_schema(files):
    datadir = '../data/'

    result = {}
    for file in files:
        with open(datadir + file, 'r') as input:
            data = json.load(input)
        for record in data:
            result[record] = data[record]['schema']

    return result


def construct_check_attrs(file):
    with open(file, 'r') as check:
        check_data = json.load(check)
    result = {}
    for item in check_data:
        result[item[0]] = item[1]
    return result


def construct_check_schema(file):
    with open(file, 'r') as check:
        check_data = json.load(check)
    result = {}
    for item in check_data:
        result[item[0]] = item[1][0]
    return result


def get_f1_attrs(results, check, attrs):
    stat = {}
    for attr in attrs:
        stat[attr] = {'tp': 0, 'fp': 0, 'fn': 0}
    stat[u'all'] = {'tp': 0, 'fp': 0, 'fn': 0}

    for record in results:
        for res_label, check_label  in zip(map(lambda x: x[1], results[record]), map(lambda x: x[1], check[record])):
            if check_label != u'junk':
                # positive
                if res_label == check_label:
                    # true
                    stat[check_label]['tp'] += 1
                    stat[u'all']['tp'] += 1
                else:
                    # false
                    stat[check_label]['fp'] += 1
                    stat[u'all']['fp'] += 1
            elif res_label != check_label:
                    # false negative
                    stat[res_label]['fn'] += 1
                    stat[u'all']['fn'] += 1

    res_stat = {}
    for item in stat:
        if stat[item]['tp'] != 0:
            prec = stat[item]['tp'] * 1.0 / (stat[item]['tp'] + stat[item]['fp'])
            rec = stat[item]['tp'] * 1.0 / (stat[item]['tp'] + stat[item]['fn'])
            f1 = 2 * prec * rec / (prec + rec)
            res_stat[item] = {'Precision': prec, 'Recall': rec, 'F1': f1}
        else:
            res_stat[item] = {'Precision': 0.0, 'Recall': 0.0, 'F1': 0.0}

    return res_stat


def get_accuracy_schema(results, check):
    right = 0
    for record in results:
        for res_schema, check_schema  in zip(map(lambda x: x[1], results[record]), map(lambda x: x[1], check[record])):
            # if check_label != u'junk':
            #     # positive
            #     if res_label == check_label:
            #         # true
            #         stat[check_label]['tp'] += 1
            #         stat[u'all']['tp'] += 1
            #     else:
            #         # false
            #         stat[check_label]['fp'] += 1
            #         stat[u'all']['fp'] += 1
            # elif res_label != check_label:
            #         # false negative
            #         stat[res_label]['fn'] += 1
            #         stat[u'all']['fn'] += 1
            pass

    res_stat = {}
    for item in stat:
        if stat[item]['tp'] != 0:
            prec = stat[item]['tp'] * 1.0 / (stat[item]['tp'] + stat[item]['fp'])
            rec = stat[item]['tp'] * 1.0 / (stat[item]['tp'] + stat[item]['fn'])
            f1 = 2 * prec * rec / (prec + rec)
            res_stat[item] = {'Precision': prec, 'Recall': rec, 'F1': f1}
        else:
            res_stat[item] = {'Precision': 0.0, 'Recall': 0.0, 'F1': 0.0}

    return res_stat


if __name__ == '__main__':
    files = ['res1.json', 'res2.json', 'res3.json', 'res4.json']
    # res_attrs = construct_results_attrs(files)
    # check_attrs = construct_check_attrs('../data/check_19130.txt')
    res_schema = construct_results_schema(files)
    check_schema = construct_check_attrs('../data/check.json')

    attrs = [u'author', u'title', u'journal', u'year', u'pages']

    # stat = get_f1_attrs(res_attrs, check_attrs, attrs)
    #
    # for stat_val in stat:
    #     print stat_val
    #     print '\tPrecision :', stat[stat_val]['Precision']
    #     print '\tRecall :', stat[stat_val]['Recall']
    #     print '\tF1-measure :', stat[stat_val]['F1']

    acc = get_accuracy_schema(res_schema, check_schema, attrs)

    print acc

    print 'Yay!'

