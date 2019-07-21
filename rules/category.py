#!./env python

### pre-defined categories
# from collections import defaultdict
surrouding_dict = dict()
surrouding_dict['indoor'] = {'concrete': ['furniture', 'appliance', 'wall', 'other'], 'abstract': ['chart', 'art']}
surrouding_dict['outdoor'] = {'city': ['street', 'building', 'vehicle'], 'field':['park', 'nature']}
# print(surrouding_dict)

person_dict = dict()
person_dict['person'] = [{'stand': ['lean', 'back', 'front']}, 'sit', 'sport', 'show', 'gesture']
person_dict['interact'] = ['office', 'notion', 'family', 'social', 'travel', 'recreation']
# print(person_dict)
