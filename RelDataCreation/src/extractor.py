from sklearn.linear_model import LogisticRegression
import sys
import pickle
from copy import deepcopy
import numpy as np
from os.path import exists
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC

from distance import jaccard
from jellyfish import levenshtein_distance as levenshtein
from jellyfish import jaro_winkler
from jellyfish import porter_stem
from jellyfish import soundex
from metrics import smith_waterman


class PostExplorer():
    def __init__(self, rs, store, numofattr, schema_model, svm_cnt, attr_model, multisvm_cnt, decoder):
        self.count = numofattr
        self.attributes = []
        for cand in rs:
            for attr_name in cand:
                if attr_name not in self.attributes:
                    self.attributes.append(attr_name)
        if exists(schema_model):
            with open(schema_model, "rb") as model:
                self.schema_classifier = pickle.load(model)
        else:
            self.schema_classifier = SVC(kernel='linear', probability=True)
            self.svm_train(store, 1, svm_cnt)
            with open(schema_model, "wb") as model:
                pickle.dump(self.schema_classifier, model)
        if exists(attr_model):
            with open(attr_model, "rb") as model:
                self.attr_classifier = pickle.load(model)
            with open(decoder, "rb") as file:
                self.attr_code = pickle.load(file)
        else:
            # self.attr_classifier = OneVsRestClassifier(SVC(kernel='linear', probability=True), n_jobs=-1)
            self.attr_classifier = LogisticRegression()
            self.multisvm_train(store, 1, multisvm_cnt)
            with open(attr_model, "wb") as model:
                pickle.dump(self.attr_classifier, model)
            with open(decoder, "wb") as file:
                pickle.dump(self.attr_code, file)

    def create_scores(self, str1, str2, tok_sc=True):
        vector = []

        # token scores
        if tok_sc:
            vector.append(jaccard(str1.split(" "), str2.split(" ")))

        # edit scores
        str1 = unicode(str1)
        str2 = unicode(str2)
        vector.append(levenshtein(str1, str2))
        vector.append(smith_waterman(str1, str2))
        vector.append(1 - jaro_winkler(str1, str2))

        # other scores
        tokstr1 = " ".join([porter_stem(tok) for tok in str1.split(" ")])
        tokstr2 = " ".join([porter_stem(tok) for tok in str2.split(" ")])
        vector.append(levenshtein(tokstr1, tokstr2))
        sndstr1 = unicode(" ".join([soundex(tok) for tok in str1.split(" ")]))
        sndstr2 = unicode(" ".join([soundex(tok) for tok in str2.split(" ")]))
        vector.append(levenshtein(sndstr1, sndstr2))
        return vector

    def create_RLscores(self, str1, str2):
        return self.create_scores(str1, str2)

    def create_IEscores(self, str1, str2):
        return self.create_scores(str1, str2, tok_sc=False)

    def create_features(self, text, cand, rl=True):
        cand_features = []
        if self.count < len(self.attributes):
            numofattr = self.count
        else:
            numofattr = len(self.attributes)
        for ind in xrange(numofattr):
            for attr_name in cand:
                if self.attributes[ind] == attr_name:
                    if rl:
                        vector = self.create_RLscores(text, cand[attr_name])
                    else:
                        vector = self.create_IEscores(text, cand[attr_name])
                    break
            else:
                if rl:
                    vector = self.create_RLscores(text, "")
                else:
                    vector = self.create_IEscores(text, "")
            cand_features.extend(vector)
        if rl:
            vector = self.create_RLscores(text, " ".join(cand.values()))
            cand_features.extend(vector)
        return cand_features

    def createV_rl(self, post, cand):
        return self.create_features(post, cand)

    def createV_ie(self, token, cand):
        return self.create_features(token, cand, rl=False)

    def binary_rescoring(self, vectors):
        for ind in xrange(len(vectors[0])):
            min_elem = sys.maxint
            for vector in vectors:
                if vector[ind] < min_elem:
                    min_elem = vector[ind]
            for v_ind in xrange(len(vectors)):
                if vectors[v_ind][ind] == min_elem:
                    vectors[v_ind][ind] = 1.0
                else:
                    vectors[v_ind][ind] = 0.0
        return vectors

    def svm_train(self, store, begin, end):
        vectors = []
        targets = []
        for ind in xrange(begin - 1, end):
            vectors.append(self.createV_rl(store.get_names()[ind], store.get_base()[ind]))  # positive example
            targets.append(1)
            vectors.append(self.createV_rl(store.get_names()[begin + end - 2 - ind], store.get_base()[ind]))  # negative
            targets.append(-1)
            print ind, end - 1
        features = self.binary_rescoring(vectors)
        self.schema_classifier.fit(features, targets)

    def svm_predict(self, post, cands):
        vectors = []
        for cand in cands:
            vectors.append(self.createV_rl(post.content, cand))
        features = self.binary_rescoring(vectors)
        predictions = self.schema_classifier.predict_proba(features)
        max_proba = 0
        schema_index = 0
        for ind in xrange(len(predictions)):
            if predictions[ind][0] > max_proba:
                max_proba = predictions[ind][0]
                schema_index = ind
        return cands[schema_index]

    def multisvm_train(self, store, begin, end):
        vectors = []
        classes = []
        if self.count < len(self.attributes):
            numofattr = self.count
        else:
            numofattr = len(self.attributes)
        print "Training MultiSVM"
        for ind in xrange(begin - 1, end):
            for attr_name in store.get_base()[ind]:
                for attr_ind in xrange(numofattr):
                    if self.attributes[attr_ind] == attr_name:
                        tokens = store.get_base()[ind][attr_name].split(" ")
                        if tokens:
                            for token in tokens:
                                vectors.append(np.array(self.createV_ie(token, store.get_base()[ind])))
                                classes.append(attr_name)
                            break
            print ind, end - 1
        self.attr_code = {}
        encoding = {}
        for one_class in classes:
            if one_class not in encoding:
                index = len(encoding)
                encoding[one_class] = index
                self.attr_code[index] = one_class
        targets = [None] * len(classes)
        for ind in xrange(len(classes)):
            # targets[ind] = np.array([0] * len(encoding))
            # targets[ind][encoding[classes[ind]]] = 1
            targets[ind] = encoding[classes[ind]]
        vectors = np.array(vectors)
        targets = np.array(targets)
        print vectors.shape, targets.shape
        self.attr_classifier.fit(vectors, targets)

    def multisvm_predict(self, post, schema):
        vectors = []
        tokens = post.content.split(" ")
        for token in tokens:
            vectors.append(np.array(self.createV_ie(token, schema)))
        predictions_prob = self.attr_classifier.predict_proba(np.array(vectors))
        predictions = []
        for prediction in predictions_prob:
            predictions.append(prediction.argmax())
        return predictions

    def clean_attr(self, tokens, token_indices, attr):
        if attr == None:
            for ind in token_indices:
                token_indices[ind] = -1
            return token_indices
        removing_candidate = -1
        whole_attr = " ".join(tokens)
        jac_base = jaccard(whole_attr.split(" "), attr.split(" "))
        jarwin_base = jaro_winkler(whole_attr, attr)
        attr_tokens = [(tokens[ind], ind) for ind in xrange(len(tokens))]
        processing = True
        while processing:
            processing = False
            for cand_ind in xrange(len(attr_tokens)):
                whole_attr = deepcopy(attr_tokens)
                whole_attr.remove(attr_tokens[cand_ind])
                whole_attr = " ".join([token[0] for token in whole_attr])
                cur_jac = jaccard(whole_attr.split(" "), attr.split(" "))
                cur_jarwin = jaro_winkler(whole_attr, attr)
                if cur_jac < jac_base and cur_jarwin < jarwin_base:
                    removing_candidate = cand_ind
                    jac_base = cur_jac
                    jarwin_base = cur_jarwin
            if removing_candidate != -1:
                processing = True
                token_indices[attr_tokens[removing_candidate][1]] = -1
                attr_tokens.remove(attr_tokens[removing_candidate])
                removing_candidate = -1
        if jac_base > 0.85 and jarwin_base > 0.85:
            for ind in token_indices:
                token_indices[ind] = -1
        return token_indices

    def results(self, post, labels, schema, res_file):
        tokens = post.content.split(" ")
        label_list = []
        for label in labels:
            if label not in label_list:
                label_list.append(label)
        for label in label_list:
            attr_tokens = []
            token_indices = {}
            for ind in xrange(len(labels)):
                if label == labels[ind]:
                    attr_tokens.append(tokens[ind])
                    token_indices[ind] = label
            token_indices = self.clean_attr(attr_tokens, token_indices, schema[self.attr_code[label]])
            for ind in token_indices:
                labels[ind] = token_indices[ind]
        self.attr_code[-1] = "junk"
        output = ""
        for ind in xrange(len(tokens)):
            output += tokens[ind] + " " + self.attr_code[labels[ind]] + "\n"
        output += "\n"
        with open(res_file, "at") as res:
            res.write(output)
