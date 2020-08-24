import os
from ast import literal_eval

dir_TP_annotated_conll = 'out'
dir_FN_annotated = 'framenet_annotated'

FN_annotated_list = list()

files = os.listdir(dir_FN_annotated)
for file in files:
    with open(dir_FN_annotated + '/' + file, 'r') as f:
        dict_ann = literal_eval(f.read())
        FN_annotated_list.append(dict_ann)

