import MySQLdb
from abc import ABCMeta, abstractmethod
from sys import stdout


class DataBaseManager:
    def __init__(self, db_info):
        self.url = db_info['url']
        self.db_name = db_info['db']
        self.login = db_info['login']
        self.pswd = db_info['pswd']
        self.db = None
        self.cursor = None

    def _open_conn(self):
        self.db = MySQLdb.connect(host=self.url,
                                  db=self.db_name,
                                  user=self.login,
                                  passwd=self.pswd,
                                  charset='utf8')
        self.cursor = self.db.cursor()

    def _close_conn(self):
        self.db.close()

    def _exec_query(self, query):
        try:
            self.cursor.execute(query)
            if query.startswith('INSERT'):
                self.db.commit()
            return self.cursor.fetchall()
        except:
            print 'Error while processing SQL-query %s' % query
            raise

    def _schema_exists(self, schemaname):
        query = 'SHOW DATABASES LIKE \'{0}\''.format(schemaname)
        res = self._exec_query(query)
        if res:
            return True
        return False


class TableManager(DataBaseManager):
    def __init__(self, db_info):
        DataBaseManager.__init__(self, db_info)

    def _clear_table(self, name):
        self._open_conn()
        query = 'DELETE FROM {0}'.format(name)
        self._exec_query(query)
        self._close_conn()

    def _ins_stmt(self, table, values):
        name, attrs = table.items()[0]
        stmt = u'INSERT INTO {0} ({1}) VALUES ({2})'

        def word_wrapper(word):
            if word and len(word) > 400:
                word = word[:400]
            if word is None:
                return u'Null'
            else:
                return u'\'{0}\''.format(word.replace('\'', '\\\''))
        stmt = stmt.format(name,
                           ', '.join(attrs),
                           ', '.join(map(word_wrapper, values)))
        del word_wrapper

        return stmt


class BSLManager(DataBaseManager):
    def __init__(self, db_info, schema_name):
        DataBaseManager.__init__(self, db_info)
        self.db_info = db_info
        self.schema_name = schema_name
        self.dtable = DataTable(self.db_info, self.schema_name)
        self.mtable = MatchTable(self.db_info, self.schema_name)

    def _create_schema(self, recreate=False):
        self._open_conn()
        exist = self._schema_exists(self.schema_name)
        if not exist or recreate:
            if exist:
                # recreate
                query = 'DROP SCHEMA {0}'.format(self.schema_name)
                self._exec_query(query)
            query = 'CREATE SCHEMA {0} DEFAULT CHARACTER SET utf8'.format(self.schema_name)
            self._exec_query(query)
            self.dtable.create_db()
            self.mtable.create_db()
        self._close_conn()

    def _clear_db(self):
        # !!! First match tables - they have foreign key constraints
        self.mtable._clear_tables()
        self.dtable._clear_tables()

    def fill_db(self, data, recreate=True):
        self._create_schema(recreate=recreate)
        print 'Database \'{0}\' created.'.format(self.schema_name)
        #TODO clearing
        # self._clear_db()
        # print 'Database cleared.'
        self.dtable.fill_db(data)
        self.mtable.fill_db(data)

    def get_cands(self):
        fc_info = self.mtable.get_finalcands_info()
        cands = self.dtable.get_cands(fc_info)

        return cands


class IDataSet():
    __metaclass__=ABCMeta

    @abstractmethod
    def create_db(self):
        pass

    @abstractmethod
    def fill_db(self, samples_file):
        pass


class DataTable(TableManager, IDataSet):
    def __init__(self, db_info, schema_name):
        TableManager.__init__(self, db_info)
        self.schema_name = schema_name

    def create_db(self):
        self._open_conn()
        if not self._schema_exists(self.schema_name):
            raise SystemError('Database {0} does not exist.'.format(self.schema_name))
        query = 'USE bsl_papers'
        self._exec_query(query)

        # equal schema for all information databases
        create_tmplt = 'CREATE TABLE {0} (' \
                           '`id_{1}` VARCHAR(10) NOT NULL, ' \
                           '`author` VARCHAR(400) NULL, ' \
                           '`title` VARCHAR(400) NULL, ' \
                           '`journal` VARCHAR(400) NULL, ' \
                           '`year` VARCHAR(400) NULL, ' \
                           '`pages` VARCHAR(400) NULL, ' \
                           'PRIMARY KEY (`id_{1}`));\n'

        query = create_tmplt.format('attrs', 'attrs')
        query += create_tmplt.format('linkstrain', 'link')
        query += create_tmplt.format('linkstest', 'link')
        self._exec_query(query)
        self._close_conn()

    def _clear_tables(self):
        self._clear_table('{0}.attrs'.format(self.schema_name))
        self._clear_table('{0}.linkstrain'.format(self.schema_name))
        self._clear_table('{0}.linkstest'.format(self.schema_name))

    def _table_schema(self, table, attrs):
        table_schema = [table['id']]
        table_schema.extend(attrs)
        return {table['name']: tuple(table_schema)}

    def _construct_attrs_values(self, ind, sample):
        id = str(ind)
        author = sample.get('author')
        title = sample.get('title')
        journal = sample.get('journal')
        year = sample.get('year')
        pages = sample.get('pages')
        return (id, author, title, journal, year, pages)

    def _construct_links_values(self, ind, sample):
        return (str(ind), sample, sample, sample, sample, sample)

    def fill_db(self, data):
        self._open_conn()
        table_attrs = {'name': '{0}.attrs'.format(self.schema_name),
                       'id': 'id_attrs'}
        table_links_train = {'name': '{0}.linkstrain'.format(self.schema_name),
                             'id': 'id_link'}
        table_links_test = {'name': '{0}.linkstest'.format(self.schema_name),
                            'id': 'id_link'}

        schema_tmplt = ('author', 'title', 'journal', 'year', 'pages')

        # metadata table
        print 'Filling {0}'.format(table_attrs['name'])
        progr = 0
        for item in data['attrs']:
            progr += 1
            table = self._table_schema(table_attrs, schema_tmplt)
            values = self._construct_attrs_values(item['id'], item['data'])
            ins_query = self._ins_stmt(table, values)
            self._exec_query(ins_query)
            stdout.write('\rProgress:  {0}/{1}'.format(progr, len(data['attrs'])))
            stdout.flush()
        else:
            message = '\rProgress:  {0}/{1}  Complete\n'
            stdout.write(message.format(progr, len(data['attrs'])))
            stdout.flush()

        # posts train table
        print 'Filling {0}'.format(table_links_train['name'])
        progr = 0
        for item in data['train']:
            progr += 1
            table = self._table_schema(table_links_train, schema_tmplt)
            values = self._construct_links_values(item['id'], item['data'])
            ins_query = self._ins_stmt(table, values)
            self._exec_query(ins_query)
            stdout.write('\rProgress:  {0}/{1}'.format(progr, len(data['train'])))
            stdout.flush()
        else:
            message = '\rProgress:  {0}/{1}  Complete\n'
            stdout.write(message.format(progr, len(data['train'])))
            stdout.flush()

        # posts test table
        print 'Filling {0}'.format(table_links_test['name'])
        progr = 0
        for item in data['test']:
            progr += 1
            table = self._table_schema(table_links_test, schema_tmplt)
            values = self._construct_links_values(item['id'], item['data'])
            ins_query = self._ins_stmt(table, values)
            self._exec_query(ins_query)
            stdout.write('\rProgress:  {0}/{1}'.format(progr, len(data['test'])))
            stdout.flush()
        else:
            message = '\rProgress:  {0}/{1}  Complete\n'
            stdout.write(message.format(progr, len(data['test'])))
            stdout.flush()

        self._close_conn()

    def _select(self, what, from_db, id, ind):
        self._open_conn()

        query = 'SELECT {1} FROM {0}.{2} WHERE {3} = {4}'
        res = self._exec_query(query.format(self.schema_name, what, from_db, id, ind))

        self._close_conn()
        return res

    def get_cands(self, fc_info):
        fcands = []
        for post_ind in fc_info:
            sample = {}
            post = self._select('author', 'linkstest', 'id_link', post_ind)
            sample['post'] = post[0][0]  # result of query is tuple with length 1
            sample['cands'] = []
            for cand_ind in fc_info[post_ind]:
                meta_info = self._select('*', 'attrs', 'id_attrs', cand_ind)
                meta_info = meta_info[0]  # result of query is tuple with length 1
                meta = {}
                meta['author'] = meta_info[1]
                meta['title'] = meta_info[2]
                meta['journal'] = meta_info[3]
                meta['year'] = meta_info[4]
                meta['pages'] = meta_info[5]
                sample['cands'].append(meta)
            fcands.append(sample)
        return fcands


class MatchTable(TableManager, IDataSet):
    def __init__(self, dbinfo, schema_name):
        TableManager.__init__(self, dbinfo)
        self.schema_name = schema_name

    def create_db(self):
        self._open_conn()
        if not self._schema_exists(self.schema_name):
            raise SystemError('Database {0} does not exist.'.format(self.schema_name))
        query = 'USE bsl_papers'
        self._exec_query(query)

        # equal schema for all match databases
        create_tmplt = 'CREATE TABLE {0} (' \
                           '`id_{2}` VARCHAR(10) NOT NULL, ' \
                           '`id_{1}` VARCHAR(10) NOT NULL, ' \
                           'PRIMARY KEY (`id_{2}`, `id_{1}`));\n'

        query = create_tmplt.format('linkstrain_attrs_MATCHES',
                                    'attrs',
                                    'link',
                                    'attrs',
                                    'linkstrain')
        query += create_tmplt.format('linkstrain_finalCANDS',
                                     'attrs',
                                     'link',
                                     'attrs',
                                     'linkstrain')
        query += create_tmplt.format('linkstest_finalCANDS',
                                     'attrs',
                                     'link',
                                     'attrs',
                                     'linkstest')
        self._exec_query(query)
        self._close_conn()

    def _clear_tables(self):
        self._clear_table('{0}.linkstrain_attrs_MATCHES'.format(self.schema_name))
        self._clear_table('{0}.linkstrain_finalCANDS'.format(self.schema_name))
        self._clear_table('{0}.linkstest_finalCANDS'.format(self.schema_name))

    def _table_schema(self, name):
        return {name: ('id_link', 'id_attrs')}

    def fill_db(self, data):
        self._open_conn()
        table_matches = '{0}.linkstrain_attrs_MATCHES'.format(self.schema_name)

        # match table
        print 'Filling {0}'.format(table_matches)
        progr = 0
        for item in data['matches']:
            progr += 1
            table = self._table_schema(table_matches)
            ins_query = self._ins_stmt(table, (str(item['link']), str(item['attrs'])))
            self._exec_query(ins_query)
            self.db.commit()
            stdout.write('\rProgress:  {0}/{1}'.format(progr, len(data['matches'])))
            stdout.flush()
        else:
            message = '\rProgress:  {0}/{1}  Complete\n'
            stdout.write(message.format(progr, len(data['matches'])))
            stdout.flush()

        # final tables are completed by BSL
        self._close_conn()

    def _select_fc(self):
        self._open_conn()

        query = 'SELECT * FROM {0}.linkstest_finalCANDS'.format(self.schema_name)
        res = self._exec_query(query)

        self._close_conn()
        return res

    def get_finalcands_info(self):
        res_q = self._select_fc()

        res = {}
        for id_link, id_attrs in res_q:
            if id_link in res:
                res[id_link].append(id_attrs)
            else:
                res[id_link] = [id_attrs]

        return res


def data_convert(train_data, test_data):
    # Compute indices for DB-managers.
    # DB-managers get full data to export it to database.
    attrs = []
    train = []
    test = []
    matches = []

    # Some samples contain equal metadata.
    # Database contains only one item per unique metadata.
    # Text posts are all unique.
    samples_met = {}

    for sample in train_data:
        # sample is a pair of metadata and text post
        if str(sample['attr']) in samples_met:
            attrs_ind = samples_met[str(sample['attr'])]
        else:
            attrs_ind = len(samples_met)
            samples_met[str(sample['attr'])] = attrs_ind
            attrs.append({'id': attrs_ind, 'data': sample['attr']})
        train_ind = len(train)
        train.append({'id': train_ind, 'data': sample['name']})
        matches.append({'link': train_ind, 'attrs': attrs_ind})

    for sample in test_data:
        test.append({'id': len(test), 'data': sample['name']})

    return {'attrs': attrs, 'train': train, 'test': test, 'matches': matches}
