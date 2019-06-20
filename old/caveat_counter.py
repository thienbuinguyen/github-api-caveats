import glob
import json

files = glob.glob('./api_caveat_sentences/*.json')
entities = 0
class_level_api_sent = 0
caveat_sent = 0
caveat_misc = 0

for file in files:
    with open(file) as f:
        obj = json.load(f)
        entities += len(obj)
        for api in obj:
            if 'class_level_caveat_sentences' in api:
                class_level_api_sent += len(api['class_level_caveat_sentences'])
            else:
                caveat_sent += len(api['caveat_sentences'])
                caveat_misc += len(api['caveat_misc'])

print('APIs/entities: {}'.format(entities))
print('Class level: {}'.format(class_level_api_sent))
print('Caveat sentences: {}'.format(caveat_sent))
print('Misc caveat sentences: {}'.format(caveat_misc))
print('Total: {}'.format(class_level_api_sent + caveat_sent + caveat_misc))

