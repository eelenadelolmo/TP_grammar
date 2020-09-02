import os
import re
import natsort
import shutil
import webbrowser
from conllu import parse
import pyconll as pc
from ast import literal_eval
from itertools import tee, islice, chain


# Given a string composed of one or several tokens and a sentence
# Returns the ordered list of ids of the tokens in the sentence
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


# Given a sentence
# Returns the subtree composed of the theme and rheme of its main clause
def keep_theme_rheme(sent):

    lines = sent.split('\n')
    main = ""

    for line in lines:
        line_fields = line.split('\t')
        if len(line_fields)>=5 and ("t=yes" in line_fields[5] or "r=yes" in line_fields[5]):
            main += line + '\n'

    return main


# Transforms a conllu sentence into the string with its forms
def txt_transformer(file_conllu):
    s_list = list()
    with open(file_conllu, 'r') as f:
        lines = f.readlines()
        ok = ""
        for l in lines:
            if len(l) > 1:
                line_ok = l[:-1] + '\t_\t_\n'
                ok += line_ok
            else:
                ok += l
    conll = pc.load_from_string(ok)
    for s in conll:
        s_txt = ""
        for word in s[:-1]:
            s_txt = s_txt + " " + word.form
        s_txt = s_txt + ".\n"
        s_list.append(s_txt)
    return s_list


def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)


# def xml_transformer(text):
# PENDING


# Input dirs
dir_FN_annotated = 'framenet_annotated'
dir_TP_annotated = 'grew_annotated'

# Output dir for conllu
dir_output = 'out_fm'
shutil.rmtree(dir_output, ignore_errors=True)
os.makedirs(dir_output)

# Output dir for svg
dir_svg = 'svg_fm'
shutil.rmtree(dir_svg, ignore_errors=True, onerror=None)
os.makedirs(dir_svg)

# Output dir for html
dir_html = 'template_fm'
shutil.rmtree(dir_html, ignore_errors=True, onerror=None)
os.makedirs(dir_html)


# List of FrameNet annotations (one list element per sentence)
FN_annotated_list = list()

## Data structure:
# - Every FrameNet annotation consist of a Python dictionary with
# Key: a Python tuple (type of frame, head string)
# Value: list of arguments
# - Every argument is a Python tuple (type of FrameNet relation, string)


# Getting the ordered list with the FrameNet annotations for every sentence
files_fm = (os.listdir(dir_FN_annotated))
for file in files_fm:
    with open(dir_FN_annotated + '/' + file, 'r') as f:
        dict_ann = literal_eval(f.read())
        FN_annotated_list.append(dict_ann)

file_grew = os.listdir(dir_TP_annotated)[0]
n_sentence = 0

with open(dir_TP_annotated + '/' + file_grew) as f:
    sentences = parse(f.read())

    fm_annotated = ""
    for sentence in sentences:

        sentence_main = keep_theme_rheme(sentence.serialize())
        fm_anns = FN_annotated_list[n_sentence]
        n_sentence += 1

        # Getting the ids of the tokens conforming the head of a FrameNet frame
        for ann_head in fm_anns:
            ann = ann_head[0]
            head = ann_head[1]
            h_id = search_id(head, sentence.serialize())

        fm_annotated += sentence_main + '\n'


    # Creating the HTML file in the template folder
    with open(dir_output + '/' + file_grew, "w") as h:
        h.write(fm_annotated)
        h.close()


## Obtaing CSV trees from conllu annotations

# For relative commands execution
os.chdir("/home/elena/PycharmProjects/TP_grammar/venv/main")

# Prepared for executing with a list of files
nombres_textos = os.listdir(dir_output)
for nombre in nombres_textos:

    os.makedirs(dir_svg + '/' + nombre)
    ruta_input = dir_output + '/' + nombre

    # Deleting unnecessary features
    with open(ruta_input, 'r+') as f:
        raw = f.read()
        raw = re.sub('whatever','', raw)
        f.close()
    with open(ruta_input, 'w') as f:
        f.write(raw)

    comando_gen = 'python3 conll_viewer/dependency2tree.py -o svg_fm/' + nombre + '/' + nombre + '.svg -c ' + ruta_input + ' --ignore-double-indices --feats'
    os.system(comando_gen)


## Colouring specific nodes

# Creating the dictionary of annotation types and the corresponding color for the ellipses containing that feature
colors = {'t': '#BEDA48', 'r': '#EBAD84'}

# Selecting the SVG files to color
for nombre in nombres_textos:

    outputdir_img = dir_svg + '/' + nombre
    nombres_frases = os.listdir(outputdir_img)
    for nombre_frase in nombres_frases:

        for key in colors:
            color = colors[key]

            # Conllu transformation of the GRS output unordered graph
            with open(outputdir_img + '/' + nombre_frase, "r+") as f:
                original_xml = f.read()
                f.seek(0)
                g_objects = original_xml.split('-->')
                g_objects_colored = list()
                for g_object in g_objects:
                    if key + '=yes' in g_object:
                        g_object = re.sub('fill="none', 'fill="' + color, g_object)
                        g_objects_colored.append(g_object)
                    else:
                        g_objects_colored.append(g_object)

                colored_xml = '-->'.join(g_objects_colored)
                f.write(colored_xml)


## Generating one HTML file with the original and rewriten trees of every text

for nombre in nombres_textos:
    html = """<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Drawing the trees for the sentences in the text</title>

        <style>
        </style>

    </head>

    <body>

        <div>
    """

    text_sentences = txt_transformer(dir_output + '/' + nombre)

    # Creating lists of names for the different types of SVG files
    outputdir_img = dir_svg + '/' + nombre
    nombres_imgs = os.listdir(outputdir_img)

    n_sentence = 0
    img_html = ""
    nombres_imgs = natsort.natsorted(nombres_imgs)

    for nombre_img in nombres_imgs:
        img_html = img_html + '\t\t\t' + '<p>' + text_sentences[n_sentence] + '</p>' + '\n\t\t\t<a href="../svg_fm/' + nombre + '/' + nombre_img + '" target="_blank"><img src="../svg_fm/' + nombre + '/' + nombre_img + '" border="1" width="100%"></a>' + '\n'
        n_sentence += 1

    html = html + '\n' + img_html + """
        </div>

    </body>
</html>
    """

    # Creating the HTML file in the template folder
    with open(dir_html + '/' + nombre + '.html', "w") as h:
        h.write(html)


# Opening a new tab in browser with the results for selected texts
texts_to_show_after_execution = [
    '1_20000702_ssd_annotated_recursive.conllu'
]
for text in texts_to_show_after_execution:
    webbrowser.open(dir_html + '/' + text + '.html', new=1, autoraise=True)
