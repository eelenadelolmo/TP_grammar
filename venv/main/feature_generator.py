import os
import natsort
from conllu import parse
from ast import literal_eval
from itertools import tee, islice, chain

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

dir_FN_annotated = 'framenet_annotated'
dir_TP_annotated = 'grew_annotated'

def search_id(toks, sent):
    lines = sent.split('\n')
    toks_list = toks.split(' ')
    ids = list()
    for token in toks_list:
        for line in lines:
            if len(line)>1 and token == line.split('\t')[1]:
                ids.append(line.split('\t')[0])

    if len(ids) > len(toks_list):
        matches = 1
        ids_copy = ids[:]
        sig = ""
        for x in ids_copy:
            if matches == len(toks_list):
                until = matches-1
                ids = ids[:until]
                ids.append(sig)
                break
            sig = str(int(x) + 1)
            if sig not in ids[1:]:
                ids.remove(x)
            else:
                matches += 1
            if len(ids) == len(toks_list):
                break

    """
    while len(ids) > len(toks_list):
        for _, x, next in previous_and_next(ids):
            if next is None:
                break
            elif int(next) < int(x):
                ids.remove(next)
            elif int(next) != int(x)+1:
                ids.remove(x)
    """

    return ids


FN_annotated_list = list()

files_fm = natsort.natsorted(os.listdir(dir_FN_annotated))
for file in files_fm:
    with open(dir_FN_annotated + '/' + file, 'r') as f:
        dict_ann = literal_eval(f.read())
        FN_annotated_list.append(dict_ann)

file_grew = os.listdir(dir_TP_annotated)[0]
n_sentence = 0

with open(dir_TP_annotated + '/' + file_grew) as f:
    sentences = parse(f.read())

    for sentence in sentences:
        fm_anns = FN_annotated_list[n_sentence]
        n_sentence += 1

        for ann_head in fm_anns:
            ann = ann_head[0]
            head = ann_head[1]
            h_id = search_id(head, sentence.serialize())
            print(head, h_id)
