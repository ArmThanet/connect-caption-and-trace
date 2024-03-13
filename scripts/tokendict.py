"""
Preprocess a raw json dataset into hdf5/json files for use in data_loader.py

Input: json file that has the form
[{ file_path: 'path/img.jpg', captions: ['a caption', ...] }, ...]
example element in this list would look like
{'captions': ['คำอธิบายภาพ 1', 'คำอธิบายภาพ 2'], 'file_path': 'val2014/COCO_val2014_000000391895.jpg', 'id': 391895}

This script reads this json, does some basic preprocessing on the captions
(e.g. lowercase, etc.), creates a special UNK token, and encodes everything to arrays

Output: a json file and an hdf5 file
The hdf5 file contains several fields:
/labels is (M,max_length) uint32 array of encoded labels, zero padded
/label_start_ix and /label_end_ix are (N,) uint32 arrays of pointers to the 
  first and last indices (in range 1..M) of labels for each image
/label_length stores the length of the sequence for each of the M sequences

The json file has a dict that contains:
- an 'ix_to_word' field storing the vocab in form {ix:'word'}, where ix is 1-indexed
- an 'images' field that is a list holding auxiliary information for each image, 
  such as in particular the 'split' it was assigned to.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json
import argparse
from random import seed
import numpy as np
import h5py


from spellchecker.spellchecker_offline import addEntry,tokenize

def build_vocab(imgs):
    counts = {}
    
    # Define your custom tokenization function here
    def split(sent):
        return tokenize(sent)
    
    for img in imgs:
        if 'caption' not in img:
            continue
        for sent in img['caption']:
            words = split(sent)
            for w in words:
                counts[w] = counts.get(w, 0) + 1

    vocab = list(counts.keys())

    total_words = sum(counts.values())

    print('total words:', total_words)
    print('number of words in vocab:', len(vocab))

    for img in imgs:
        img['final_captions'] = []
        if 'caption' not in img:
            continue
        for sent in img['caption']:
            words = split(sent)
            caption = [w for w in words if w in vocab]
            img['final_captions'].append(caption)

    return vocab




def encode_captions(imgs, params, wtoi):
    max_length = params['max_length']
    N = len(imgs)
    M = sum(len(img['final_captions']) for img in imgs)

    label_arrays = []
    label_start_ix = np.zeros(N, dtype='uint32')
    label_end_ix = np.zeros(N, dtype='uint32')
    label_length = np.zeros(M, dtype='uint32')
    caption_counter = 0
    counter = 1
    for i, img in enumerate(imgs):
        n = len(img['final_captions'])
        assert n > 0, 'error: some image has no captions'

        Li = np.zeros((n, max_length), dtype='uint32')
        for j, s in enumerate(img['final_captions']):
            label_length[caption_counter] = min(max_length, len(s))
            caption_counter += 1
            for k, w in enumerate(s):
                if k < max_length:
                    if w in wtoi:
                        Li[j, k] = wtoi[w]
                    else:
                        Li[j, k] = wtoi['UNK']

        label_arrays.append(Li)
        label_start_ix[i] = counter
        label_end_ix[i] = counter + n - 1
        counter += n
    
    L = np.concatenate(label_arrays, axis=0)
    assert L.shape[0] == M, 'lengths don\'t match? that\'s weird'
    assert np.all(label_length > 0), 'error: some caption had no words?'

    print('Encoded captions to array of size ', L.shape)
    return L, label_start_ix, label_end_ix, label_length

def main(params):
    imgs = json.load(open(params['input_json'], 'r'))
    imgs = imgs['images']  # Assuming 'images' key contains the list of images
    
    seed(123)  

    vocab = build_vocab(imgs)  # Call build_vocab with only one argument
    itow = {i + 1: w for i, w in enumerate(vocab)}  
    wtoi = {w: i + 1 for i, w in enumerate(vocab)}  

    L, label_start_ix, label_end_ix, label_length = encode_captions(imgs, params, wtoi)

    N = len(imgs)
    f_lb = h5py.File(params['output_h5'] + '_label.h5', "w")
    f_lb.create_dataset("labels", dtype='uint32', data=L)
    f_lb.create_dataset("label_start_ix", dtype='uint32', data=label_start_ix)
    f_lb.create_dataset("label_end_ix", dtype='uint32', data=label_end_ix)
    f_lb.create_dataset("label_length", dtype='uint32', data=label_length)
    f_lb.close()

    out = {}
    out['ix_to_word'] = itow  
    out['images'] = []
    for i, img in enumerate(imgs):
        jimg = {}

        if 'split' in img:
            jimg['split'] = img['split']
        else:
            jimg['split'] = 'val'

        if 'file_path' in img:
            jimg['file_path'] = img['file_path']
        else:
            print(f"Error: 'file_path' not found in image {i + 1}. Skipping.")
            continue

        if 'id' in img:
            jimg['id'] = str(img['id'])
        else:
            print(f"Warning: 'id' not found in image {i + 1}. Skipping.")

        out['images'].append(jimg)

    json.dump(out, open(params['output_json'], 'w'))
    print('wrote ', params['output_json'])




if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_json', required=True, help='input json file to process into hdf5')
    parser.add_argument('--output_json', default='data.json', help='output json file')
    parser.add_argument('--output_h5', default='data', help='output h5 file')

    parser.add_argument('--images_root', default='/mnt/c/Users/thane/Desktop/@Final/05.02.2024Detectron/detectron2/datasets/coco/val2017', help='root location in which images are stored, to be prepended to file_path in input json')

    parser.add_argument('--max_length', default=35, type=int, help='max length of a caption, in number of words. captions longer than this get clipped.')
    # parser.add_argument('--word_count_threshold', default=3, type=int, help='only words that occur more than this number of times will be put in vocab')

    args = parser.parse_args()
    params = vars(args)  
    print('parsed input parameters:')
    print(json.dumps(params, indent=2))
    main(params)
