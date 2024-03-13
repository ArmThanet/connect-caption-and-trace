import json
import argparse

def main(params):
    imgs = json.load(open(params['input_json'], 'r'))
    annotations = imgs['annotations']
    images = imgs['images']

    # Convert image_id in annotations to integers
    for annotation in annotations:
        annotation['image_id'] = int(annotation['image_id'])

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
                "file_path": "val/"+file_name,
                "id": image_id,
                "filename": file_name
            }
            output_data["images"].append(output_image)

    # Write output JSON to file
    with open(params['output_json'], 'w') as outfile:
        json.dump(output_data, outfile)

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
