__author__ = 'dandelion'

import json


file = 'data/samples.json'

with open(file, 'rt') as f:
    samples = json.load(f)

def statistic_counter(samples):
    statistics = {}
    attr_types = []
    # getting all attributes
    for sample in samples:
        for attr in sample['attr']:
            if attr not in attr_types:
                attr_types.append(attr)

    # filling statistics structure
    for attr_type in attr_types:
        statistics[attr_type] = {}

    for sample in samples:
        for attr in attr_types:
            if attr not in sample['attr']:
                if '' not in statistics[attr]:
                    statistics[attr][''] = 0
                statistics[attr][''] += 1
            elif sample['attr'][attr] not in statistics[attr]:
                statistics[attr][sample['attr'][attr]] = 1
            else:
                statistics[attr][sample['attr'][attr]] += 1
    return statistics


def print_stat(statistics):
    print 'Number of attribute types:', len(statistics)
    for attr_type in statistics:
        # statistics[attr_type] is a dictionary
        attr = statistics[attr_type].items()
        attr.sort(key=lambda x: x[1], reverse=True)
        attr_count = [0,0]
        for attr_val, count in attr:
            if attr_val != '':
                attr_count[1] += count
            attr_count[0] += count
        print attr_type, str(attr_count[1]) + '/' + str(attr_count[0])
        for attr_val, count in attr:
            if attr_val == '':
                print '\tNo value:', count
            else:
                print '\t', attr_val + ':', count


print_stat(statistic_counter(samples))

print 'Yay!'
