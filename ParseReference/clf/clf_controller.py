import os
import sys
import json
from time import time

from clf_manage import SchemaFinder, AttrsExtractor


def count_time(name, proc):
    begin_time = time()

    res = proc()

    cur_time = time()
    print 'Process \'{0}\' took {1} sec'.format(name, cur_time - begin_time)
    return (res, cur_time - begin_time)


def main(mode, datafile, resfile, path_to_model, timefile):
    datadir = path_to_model

    fold_num = datafile.split('/')[-1][4:-5]

    if not os.path.exists(datadir):
        os.makedirs(datadir)

    schema_model = 'fschema{0}.model'.format(fold_num)
    attr_model = 'exattrs{0}.model'.format(fold_num)

    if os.path.isfile(timefile):
        with open(timefile, 'r') as timef:
            process_time = json.load(timef)
    else:
        process_time = {}

    sch_f = SchemaFinder(datadir + schema_model)
    attr_ex = AttrsExtractor(datadir + attr_model)

    if mode == 'train':
        begin_time = time()

        with open(datafile, 'r') as input:
            data = json.load(input)
            train_data = data[0]
            test_data = data[1]

        process_time['clf_schema_fit'] = count_time('Schema Finder fit',
                                                    lambda: sch_f.fschema_train(train_data))[1]

        process_time['clf_attrs_fit'] = count_time('Attrs Extr fit',
                                                   lambda: attr_ex.exattrs_train(train_data))[1]

        process_time['clf_fit_total'] = time() - begin_time
        print 'Learning total took {0} sec'.format(process_time['clf_fit_total'])

        with open(timefile, 'w') as timef:
            json.dump(process_time, timef)

        return 0

    elif mode == 'parse':
        begin_time = time()

        with open(datafile, 'r') as input:
            cands = json.load(input)

        res = count_time('Find schemas',
                         lambda: sch_f.find_schema(cands))
        posts_with_schema = res[0]
        process_time['clf_schemas'] = res[1]

        res = count_time('Extract attrs',
                         lambda: attr_ex.extract_attrs(posts_with_schema))
        parsed_posts = res[0]
        process_time['clf_attrs'] = res[1]

        res = zip(posts_with_schema, parsed_posts)

        process_time['clf_parce_total'] = time() - begin_time
        print 'Parsing total took {0} sec'.format(process_time['clf_parce_total'])

        with open(resfile, 'w') as output:
            json.dump(res, output)

        with open(timefile, 'w') as timef:
            json.dump(process_time, timef)

        return 0


if __name__ == '__main__':
    mode = sys.argv[1]
    datafile = sys.argv[2]
    resfile = sys.argv[3]
    path_to_model = sys.argv[4]
    timefile = sys.argv[5]
    main(mode, datafile, resfile, path_to_model, timefile)
