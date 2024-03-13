import fileinput
import json
import time
import random
from pythainlp.util import normalize
# time at the start of the program is noted
start = time.time()
# specify the input JSON file path
json_file_path = './coco-caption/annotations/caption_human_thai_train2017.json'
# specify the output folder and file name
output_folder = './scripts/output/'
output_file_name = 'caption_human_thai_train2017.json'
# create the full path for the output file
output_file_path = output_folder + output_file_name
# open the JSON file for reading
with open(json_file_path, 'r', encoding='utf-8') as json_file:
    # load JSON data
    data = json.load(json_file)
# Function to convert Unicode to Thai
def convert_unicode_to_thai(data):
    if isinstance(data, dict):
        return {convert_unicode_to_thai(key): convert_unicode_to_thai(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_unicode_to_thai(element) for element in data]
    elif isinstance(data, str):
        return normalize(data)
    else:
        return data
# Convert Unicode to Thai
data = convert_unicode_to_thai(data)
# open the output file for writing
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    # write JSON data to the output file
    json.dump(data, output_file, indent=2, ensure_ascii=False)
# time at the end of program execution is noted
end = time.time()
# total time taken to process the JSON file
print("Execution time in seconds: ", (end - start))
# print("No. of lines written: ", num_images)
print("Output file path: ", output_file_path)
