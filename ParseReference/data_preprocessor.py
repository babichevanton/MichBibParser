import json


def reduction(datafile, resfile, keys):
    with open(datafile, 'r') as input:
        raw_data = json.load(input)

    data = []
    for sample in raw_data:
        meta = sample['attr']
        new_meta = {}
        for key in keys:
            new_meta[key] = meta.get(key)
        new_sample = {'attr': new_meta, 'name': sample['name']}
        data.append(new_sample)

    with open(resfile, 'w') as output:
        json.dump(data, output)


def data_split(datafile, resultfile, n_folds, size=None):
    with open(datafile, 'r') as input:
        samples = json.load(input)

    if size:
        samples = samples[:size]
    fold_size = len(samples) / n_folds
    split_samples = []
    split_ind = 0
    # len(samples)%n_folds last items are splitted by 1 per fold
    # so len(samples)%n_folds folds contain fold_size+1 items
    for ind in xrange(len(samples) % n_folds):
        split_samples.append(samples[split_ind:split_ind + fold_size + 1])
        split_ind += fold_size + 1
    # others folds contain fold_size items
    for ind in xrange(len(samples) % n_folds, n_folds):
        split_samples.append(samples[split_ind:split_ind + fold_size])
        split_ind += fold_size

    with open(resultfile, 'w') as output:
        json.dump(split_samples, output)


def n_un_data_split(datafile, resultfile, size=None):
    with open(datafile, 'r') as input:
        samples = json.load(input)

    if size:
        samples = samples[:size]

    meta_aligned = {}
    for sample in samples:
        str_meta = str(sorted(sample['attr'].items(), key=lambda x: x[0]))
        if str_meta in meta_aligned:
            meta_aligned[str_meta].append(sample)
        else:
            meta_aligned[str_meta] = [sample]

    test_samples = []
    train_samples = []
    for str_meta in meta_aligned:
        if len(meta_aligned[str_meta]) > 1:
            test_samples.append(meta_aligned[str_meta].pop())
            train_samples.extend(meta_aligned[str_meta])
        else:
            train_samples.extend(meta_aligned[str_meta])

    with open(resultfile, 'w') as output:
        json.dump((train_samples, test_samples), output)


def main(n_folds):
    inputfile = 'data/raw_samples.json'
    outputfile = 'data/samples.json'
    # outputfile = 'data/split_samples.json'

    keys = ('author', 'title', 'journal', 'pages', 'year')

    reduction(inputfile, outputfile, keys)
    # data_split(inputfile, outputfile, n_folds)


if __name__ == '__main__':
    main(10)
