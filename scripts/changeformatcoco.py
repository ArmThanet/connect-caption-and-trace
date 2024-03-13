"""
Preprocess a raw json dataset into a json file

Input: json file that has the form
[{ file_path: 'path/img.jpg', captions: ['a caption', ...] }, ...]
example element in this list would look like
{'captions': [u'A man with a red helmet on a small moped on a dirt road. ', u'Man riding a motor bike on a dirt road on the countryside.', u'A man riding on the back of a motorcycle.', u'A dirt path with a young person on a motor bike rests to the foreground of a verdant area with a bridge and a background of cloud-wreathed mountains. ', u'A man in a red shirt and a red hat is on a motorcycle on a hill side.'], 'file_path': u'val2014/COCO_val2014_000000391895.jpg', 'id': 391895}

This script reads this json, and generates a new JSON file with the desired structure where each image contains a list of captions along with other relevant information such as `file_path`, `id`, and `filename`.

Output: a json file

"""

import json
import argparse
# Function to decode Unicode to Thai


def main(params):
    imgs = json.load(open(params['input_json'], 'r'))
    annotations = imgs['annotations']
    images = imgs['images']

    # Group captions by image id
    image_captions = {}
    for annotation in annotations:
        image_id = annotation['image_id']
        caption = annotation['caption_thai']
        if image_id not in image_captions:
            image_captions[image_id] = []
        image_captions[image_id].append(caption)

    # Create output JSON structure
    output_data = {"images": []}
    for image in images:
        image_id = image['id']
        file_name = f"{image_id:012}.jpg"
        if image_id in image_captions:
            captions = image_captions[image_id]
            output_image = {
                "caption": captions,
                "file_path": file_name,
                "id": image_id,
                "filename": file_name
            }
            output_data["images"].append(output_image)

    # Write output JSON to file
    with open(params['output_json'], 'w') as outfile:
        json.dump(output_data, outfile, ensure_ascii=False)

    print('wrote ', params['output_json'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # input json
    parser.add_argument('--input_json', required=True, help='input json file to process into json')
    parser.add_argument('--output_json', default='data.json', help='output json file')

    args = parser.parse_args()
    params = vars(args)  # convert to an ordinary dictionary
    print('parsed input parameters:')
    print(json.dumps(params, indent=2))
    main(params)
