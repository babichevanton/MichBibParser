from copy import deepcopy


class BlockingSchemeLearner():
    def __init__(self, datastore, first, last):
        self.reference_set = deepcopy(list(set(datastore.get_base()))[first - 1:last])

    def get_rs(self):
        return self.reference_set

    def is_covering(self, cand, rule):
        for conj in rule:
            for attr_name in conj:
                if attr_name not in cand or cand[attr_name] != conj[attr_name]:
                    break
            else:
                return True
        else:
            return False

    def get_examples(self, post):
        result = []

        coeff = 0.35
        num_of_unrec_attrs = 2

        counter = 0
        unrec_attr = 0
        for cand in self.reference_set:
            counter += 1
            print counter, len(self.reference_set)
            unrec_attr = 0
            for attr_name in cand:
                if cand[attr_name] == '':
                    # attr_name is empty - shouldn't be considered
                    continue
                # find closest tokens to attribute value
                found = post.find_attr(cand[attr_name])
                found_tokens = list(set(found.split(' ')))
                attr_tokens = list(set(cand[attr_name].split(' ')))
                existing = 0
                for tok in attr_tokens:
                    if tok in found_tokens:
                        existing += 1
                if existing < len(attr_tokens) * coeff:
                    # attr didn't recognized
                    unrec_attr += 1
            if unrec_attr <= num_of_unrec_attrs:
                # cand is close enough to post
                result.append(cand)
        if not result:
            print unrec_attr

        return result

    def reduction_ratio(self, rule):
        subset = 0.0
        for cand in self.reference_set:
            if self.is_covering(cand, rule):
                subset += 1
        return 1 - subset / len(self.reference_set)

    def pair_completeness(self, rule, examples):
        if len(examples) == 0:
            return 0
        truepositives = 0
        for example in examples:
            if self.is_covering(example, rule):
                truepositives += 1
        return truepositives * 1.0 / len(examples)

    def get_attributes(self):
        attributes = {}
        for cand in self.reference_set:
            for attr_name in cand:
                for name in attributes:
                    if name == attr_name:
                        break
                else:
                    attributes[attr_name] = []
                    attributes[attr_name].append(cand[attr_name])
                    continue
                if cand[attr_name] not in attributes[attr_name]:
                    attributes[attr_name].append(cand[attr_name])
        return attributes

    def cmp_rules(self, rule1, rule2):
        if self.reduction_ratio(rule1) == self.reduction_ratio(rule2):
            return 0
        elif self.reduction_ratio(rule1) > self.reduction_ratio(rule2):
            return 1
        else:
            return -1

    def sequential_covering(self, post):
        rule = []
        examples = self.get_examples(post)
        attributes = self.get_attributes()
        conj = self.learn_one_conj(attributes, 0.5, examples, 100)
        while len(examples) > 0 and conj != {}:
            rule.append(conj)
            new_examples = deepcopy(examples)
            tmp_rule = []
            tmp_rule.append(conj)
            for i in xrange(len(examples)):
                if self.is_covering(examples[i], tmp_rule):
                    new_examples.remove(examples[i])
            examples = new_examples
            conj = self.learn_one_conj(attributes, 0.5, examples, 100)
        return rule

    def learn_one_conj(self, attributes, min_thresh, examples, beam_width):
        beam = []
        initial_conj = {}
        beam.append(initial_conj)
        res_conj = initial_conj
        step = 0
        while len(beam) > 0:
            step += 1
            print step, "step"
            new_beam = deepcopy(beam)
            for conj in beam:
                new_beam.remove(conj)
                # add all good children of conj
                for attr_name in attributes:
                    if attr_name not in conj:
                        for value in attributes[attr_name]:
                            child = deepcopy(conj)
                            child[attr_name] = value
                            child_rule = []
                            child_rule.append(child)
                            res_rule = []
                            res_rule.append(res_conj)
                            RR_child = self.reduction_ratio(child_rule)
                            RR_res = self.reduction_ratio(res_rule)
                            PC_child = self.pair_completeness(child_rule, examples)
                            if PC_child >= min_thresh and RR_child > RR_res:
                                new_beam.append(child)
            # sort by RR
            new_beam = sorted(new_beam, cmp=self.cmp_rules, reverse=True)
            print len(new_beam), "good children"
            beam = new_beam[:beam_width]
            if len(beam) > 0:
                res_conj = beam[0]
        return res_conj

    def get_candidates(self, rule):
        return [cand for cand in self.reference_set if self.is_covering(cand, rule)]
