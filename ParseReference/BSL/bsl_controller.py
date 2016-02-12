import os
import sys
import json
import subprocess
from time import time

from db_manage import BSLManager, data_convert


class WorkWithBSL():
    def __init__(self, db_info, schema_name, logfile):
        self.schema_name = schema_name
        self.logfile = logfile
        self.bsl_db = BSLManager(db_info, schema_name)
        self.subp_ex = subprocess.CalledProcessError

    def prepare_db(self, datafile):
        with open(datafile, 'r') as input:
            data = json.load(input)
            train_data = data[0]
            test_data = data[1]

        db_data = data_convert(train_data, test_data)

        print 'Start preparing DB {0}'.format(self.schema_name)
        self.bsl_db.fill_db(db_data)

    def bsl_setup(self):
        print 'Initialize BSL'
        try:
            subprocess.check_call(['./setUpRefIndex.sh', 'rs_papers.xml',
                                                         'rs_papers',
                                                         'linkstrain.xml',
                                                         'linkstrain',
                                                         'attrs.xml',
                                                         self.logfile])
        except self.subp_ex as e:
            print 'Failed: setUpRefIndex returned with {0}.'.format(e.returncode)

    def bsl_run(self):
        print 'Run BSL'
        try:
            subprocess.check_call(['./runBSL.sh', 'rs_papers.xml',
                                                  'rs_papers',
                                                  'linkstrain.xml',
                                                  'linkstrain',
                                                  'linkstest.xml',
                                                  'linkstest',
                                                  'attrs.xml',
                                                  self.logfile])
        except self.subp_ex as e:
            print 'Failed: runBSL returned with {0}.'.format(e.returncode)

    def get_cands(self, resfile):
        print 'Get candidates'
        cands = self.bsl_db.get_cands()

        with open(resfile, 'w') as output:
            json.dump(cands, output)


def count_time(name, proc):
    begin_time = time()

    proc()

    cur_time = time()
    print 'Process \'{0}\' took {1} sec'.format(name, cur_time - begin_time)
    return cur_time - begin_time


def main(datafile, resfile, timefile):
    if os.path.isfile(timefile):
        with open(timefile, 'r') as timef:
            process_time = json.load(timef)  # dict for time handling
    else:
        process_time = {}

    begin_time = time()

    db_info = {}
    db_info['url'] = 'localhost'
    db_info['db'] = ''
    db_info['login'] = 'root'
    db_info['pswd'] = '1111'
    schema_name = 'bsl_papers'
    logfile = 'bsl.log'
    wwb = WorkWithBSL(db_info, schema_name, logfile)

    process_time['bsl_db'] = count_time('Prepare DB',
                                        lambda: wwb.prepare_db(datafile))

    process_time['bsl_setup'] = count_time('BSL setUp',
                                           lambda: wwb.bsl_setup())

    process_time['bsl_run'] = count_time('BSL run',
                                         lambda: wwb.bsl_run())

    process_time['bsl_cands'] = count_time('Get cands',
                                           lambda: wwb.get_cands(resfile))

    process_time['bsl_total'] = time() - begin_time
    print 'BSL total: {0} sec'.format(process_time['bsl_total'])

    with open(timefile, 'w') as timef:
        json.dump(process_time, timef)

    return 0


if __name__ == '__main__':
    datafile = sys.argv[1]
    resfile = sys.argv[2]
    timefile = sys.argv[3]
    main(datafile, resfile, timefile)
