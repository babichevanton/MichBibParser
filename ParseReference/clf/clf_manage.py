import os
import re
import pickle
import numpy as np
from copy import copy
from string import punctuation, printable
from random import randrange
from abc import ABCMeta, abstractmethod
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

from metrics import *


class FeatureCreator:
    __metaclass__=ABCMeta

    def __init__(self):
        pass

    def _string_preprocess(self, str):
        def punkt_rem(char):
            if char in punctuation:
                return ' '
            else:
                return char

        if str is None:
            return u''

        str = ''.join(map(punkt_rem, str))
        del punkt_rem
        str = re.sub(' +', ' ', str.strip())
        str = filter(lambda x: x in printable, str)

        return u'' + str.upper()

    def _token_features(self, str1, str2):
        features = []

        # Jaccard distance
        features.append(jac_dist(str1, str2))
        #TODO Jensen-Shannon distance
        #TODO Dirichlet & Jelenic-Merser distance

        return features

    def _edit_features(self, str1, str2):
        features = []

        # Levenshtein distance
        features.append(lev_dist(str1, str2))
        # Smith-Waterman distance
        features.append(sw_dist(str1, str2))
        # Jaro-Winkler distance
        features.append(jw_dist(str1, str2))

        return features

    def _other_features(self, str1, str2):
        features = []

        # Soundex-convert distance
        features.append(snd_dist(str1, str2))
        # Porter-stemmer-convert distance
        features.append(ps_dist(str1, str2))

        return features

    @abstractmethod
    def _extract_features(self, sample):
        pass


class IClassifier():
    __metaclass__=ABCMeta

    @abstractmethod
    def _fit(self, features, targets):
        pass

    @abstractmethod
    def _predict(self, query):
        pass


class SchemaFinder(FeatureCreator, IClassifier):
    def __init__(self, modelfile):
        FeatureCreator.__init__(self)
        self.model_file = modelfile
        if os.path.isfile(modelfile):
            with open(modelfile, 'rb') as input:
                self.clf = pickle.load(input)
        else:
            self.clf = SVC(kernel='linear', probability=True)

    def _rl_scores(self, post, attr):
        features = []

        #string preprocessing
        post = self._string_preprocess(post)
        attr = self._string_preprocess(attr)

        features.extend(self._token_features(post, attr))
        features.extend(self._edit_features(post, attr))
        features.extend(self._other_features(post, attr))
        return features

    def _extract_features(self, sample):
        features = []
        for attr in sample['meta']:
            one_attr_f = self._rl_scores(sample['post'], sample['meta'][attr])
            features.extend(one_attr_f)
        all_attr = sample['meta'].values()
        for attr_ind in xrange(len(all_attr)):
            if all_attr[attr_ind] is None:
                all_attr[attr_ind] = ''
        all_attr_f = self._rl_scores(sample['post'], ' '.join(all_attr))
        features.extend(all_attr_f)
        return features

    def _binary_resc(self, features_list):
        for ind in xrange(len(features_list[0])):
            min_elem = sys.maxint
            for features in features_list:
                if features[ind] < min_elem:
                    min_elem = features[ind]
            for f_ind in xrange(len(features_list)):
                if features_list[f_ind][ind] == min_elem:
                    features_list[f_ind][ind] = 1.0
                else:
                    features_list[f_ind][ind] = 0.0
        return features_list

    def _fit(self, features_list, targets):
        self.clf.fit(features_list, targets)
        with open(self.model_file, 'wb') as model:
            pickle.dump(self.clf, model)

    def _predict(self, post_with_cands):
        features_list = []
        for cand in post_with_cands['cands']:
            ex = {'post': post_with_cands['post'],
                  'meta': cand}
            features_list.append(self._extract_features(ex))
        features_list = self._binary_resc(features_list)
        predictions = self.clf.predict_proba(features_list)
        predictions = map(lambda x: x[0], predictions.tolist())
        return post_with_cands['cands'][predictions.index(max(predictions))]

    def fschema_train(self, train_data):
        features_list = []
        targets = []
        print 'Training schema finder'

        # many posts are about the same paper - align them
        aligned_posts = {}
        for sample in train_data:
            str_meta = str(sorted(sample['attr'].items(), key=lambda x: x[0]))
            if str_meta in aligned_posts:
                aligned_posts[str_meta]['posts'].append(sample['name'])
            else:
                aligned_posts[str_meta] = {'meta': sample['attr'], 'posts': [sample['name']]}

        aligned_posts = aligned_posts.values()
        for meta_ind in xrange(len(aligned_posts)):
            # Make indices for bad example metadata
            bad_ex_inds = range(len(aligned_posts))
            # meta_ind points to the correct metadata of the post
            bad_ex_inds.pop(meta_ind)

            for post in aligned_posts[meta_ind]['posts']:
                if len(bad_ex_inds):
                    bad_ex_ind = bad_ex_inds.pop(randrange(len(bad_ex_inds)))
                else:
                    bad_ex_inds = range(len(aligned_posts))
                    bad_ex_inds.pop(meta_ind)
                    bad_ex_ind = bad_ex_inds.pop(randrange(len(bad_ex_inds)))
                good_ex = {'post': post,
                           'meta': aligned_posts[meta_ind]['meta']}
                bad_ex = {'post': post,
                          'meta': aligned_posts[bad_ex_ind]['meta']}
                features_list.append(self._extract_features(good_ex))
                targets.append(1)
                features_list.append(self._extract_features(bad_ex))
                targets.append(-1)
        features_list = self._binary_resc(features_list)
        self._fit(features_list, targets)

    def find_schema(self, queries):
        answer = []
        for query in queries:
            schema = self._predict(query)
            answer.append({'post': query['post'], 'schema': schema})
        return answer


class AttrsExtractor(FeatureCreator, IClassifier):
    def __init__(self, modelfile):
        FeatureCreator.__init__(self)
        self.model_file = modelfile
        if os.path.isfile(modelfile):
            with open(modelfile, 'rb') as model:
                model_data = pickle.load(model)
                self.classes_names = model_data[0]
                self.clf = model_data[1]
        else:
            self.classes_names = {}
            self.clf = LogisticRegression(n_jobs=-1)

    def _common_scores(self, token):
        #TODO any common scores
        return []

    def _ie_scores(self, token, attr):
        features = []

        #string preprocessing
        token = self._string_preprocess(token)
        attr = self._string_preprocess(attr)

        features.extend(self._edit_features(token, attr))
        features.extend(self._other_features(token, attr))
        return features

    def _extract_features(self, sample):
        features = []

        features.extend(self._common_scores(sample['token']))
        for attr in sample['meta']:
            features.extend(self._ie_scores(sample['token'], attr))

        return features

    def _fit(self, features_list, targets):
        np_fl = []
        for features in features_list:
            np_fl.append(np.array(features))

        self.clf.fit(np.array(np_fl), np.array(targets))

        with open(self.model_file, 'wb') as model:
            pickle.dump((self.classes_names, self.clf), model)

    def _predict(self, post_with_schema):
        features_list = []
        post_tokens = post_with_schema['post'].split(' ')
        answer = [None] * len(post_tokens)
        for token in post_tokens:
            ex = {'token': token, 'meta': post_with_schema['schema']}
            features_list.append(self._extract_features(ex))
        predictions = self.clf.predict(features_list)
        for pred_ind in xrange(len(predictions)):
            answer[pred_ind] = self.classes_names[predictions[pred_ind]]
        return answer

    def _clean_attr(self, tokens, attr_inds, attr):
        if attr is None:
            return attr_inds
        junk_inds = []
        whole_attr = u'' + ' '.join(tokens)
        attr = u'' + self._string_preprocess(attr)
        jac_base = jac_dist(whole_attr, attr)
        jw_base = jw_dist(whole_attr, attr)
        attr_tokens = [(ind, tok) for ind, tok in enumerate(tokens)]
        rem_cand = -1
        processing = True
        while processing:
            processing = False
            for cand_ind in xrange(len(attr_tokens)):
                whole_attr = copy(attr_tokens)
                whole_attr.remove(attr_tokens[cand_ind])
                whole_attr = u''+ ' '.join([token[1] for token in whole_attr])
                cur_jac = jac_dist(whole_attr, attr)
                cur_jw = jw_dist(whole_attr, attr)
                if cur_jac < jac_base and cur_jw < jw_base:
                    rem_cand = cand_ind
                    jac_base = cur_jac
                    jw_base = cur_jw
            if rem_cand != -1:
                processing = True
                junk_inds.append(attr_inds[attr_tokens[rem_cand][0]])
                attr_tokens.remove(attr_tokens[rem_cand])
                rem_cand = -1
        #TODO dynamic threshold
        if jac_base > 0.85 and jw_base > 0.85:
            return attr_inds
        return junk_inds

    def exattrs_train(self, train_data):
        features_list = []
        classes = []
        self.classes_names = {}
        classes_labels = {}
        print "Training attributes extractor"

        # assign for each attr_name it's label for classification
        meta_attrs = train_data[0]['attr'].keys()
        for ind in xrange(len(meta_attrs)):
            self.classes_names[ind] = meta_attrs[ind]
            classes_labels[meta_attrs[ind]] = ind

        for sample in train_data:
            meta = sample['attr']
            for attr in meta:
                class_label = classes_labels[attr]
                attr_str = self._string_preprocess(meta[attr])
                attr_tokens = attr_str.split(' ')
                for token in attr_tokens:
                    ex = {'token': token, 'meta': sample['attr']}
                    features_list.append(self._extract_features(ex))
                    classes.append(class_label)
        self._fit(features_list, classes)

    def extract_attrs(self, posts_with_schema):
        answer = []
        for post in posts_with_schema:
            post_text = self._string_preprocess(post['post'])
            predictions = self._predict({'post': post_text, 'schema': post['schema']})
            post_tokens = post_text.split(' ')
            junk_inds = []
            for attr in post['schema']:
                attr_inds = [i for i, lbl in enumerate(predictions) if lbl == attr]
                attr_tokens = [post_tokens[ind] for ind in attr_inds]
                junk_inds.extend(self._clean_attr(attr_tokens,
                                                  attr_inds,
                                                  post['schema'][attr]))
            for ind in junk_inds:
                predictions[ind] = 'junk'
            answer.append(zip(post_tokens, predictions))
        return answer
