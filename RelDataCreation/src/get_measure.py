import json


def construct_results(files):
    datadir = '../data/'

    result = {}
    for file in files:
        with open(datadir + file, 'r') as input:
            data = json.load(input)
        for record in data:
            result[record] = data[record]

    return result


def construct_check(file):
    with open(file, 'r') as check:
        check_data = json.load(check)
    result = {}
    for item in check_data:
        result[item[0]] = item[1]
    return result


def get_f1(results, check, attrs):
    stat = {}
    for attr in attrs:
        stat[attr] = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}
    stat[u'all'] = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}

    def get_attr(tokens, attr):
        res = []
        for tok in tokens:
            if tok[1] == attr:
                res.append(tok[0])
        return res

    for record in results:
        for attr in attrs:
            res_attr = get_attr(results[record], attr)
            check_attr = get_attr(check[record], attr)
            if check_attr:
                # positive
                if res_attr == check_attr:
                    # true
                    stat[attr]['tp'] += 1
                    stat[u'all']['tp'] += 1
                else:
                    # false
                    stat[attr]['fp'] += 1
                    stat[u'all']['fp'] += 1
            else:
                # negative
                if res_attr == check_attr:
                    # true
                    stat[attr]['tn'] += 1
                    stat[u'all']['tn'] += 1
                else:
                    # false
                    stat[attr]['fn'] += 1
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


if __name__ == '__main__':
    files = ['res1.json', 'res2.json', 'res3.json', 'res4.json']
    res = construct_results(files)
    check = construct_check('../data/test.json')
    # check = construct_check('../data/check_11034.txt')

    attrs = [u'author', u'title', u'journal', u'year', u'pages']

    stat = get_f1(res, check, attrs)

    for stat_val in stat:
        print stat_val
        print '\tPrecision :', stat[stat_val]['Precision']
        print '\tRecall :', stat[stat_val]['Recall']
        print '\tF1-measure :', stat[stat_val]['F1']

    print 'Yay!'

