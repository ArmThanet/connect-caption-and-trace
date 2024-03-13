import json

# Load the two JSON objects
with open('coco_GCC.json', 'r', encoding='utf-8') as f1, open('output-open-convert.json', 'r', encoding='utf-8') as f2:
    first_json = json.load(f1)
    second_json = json.load(f2)

# Get the list of IDs from the second JSON object
second_ids = [entry['id'] for entry in second_json['images']]

# Filter out the image entries from the first JSON object if their IDs are not present in the second JSON object
first_json['images'] = [entry for entry in first_json['images'] if entry['id'] in second_ids]

# Write the modified first JSON object back to a file
with open('modified_first_json.json', 'w', encoding='utf-8') as f:
    json.dump(first_json, f, indent=4)
