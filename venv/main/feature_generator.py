import os
import re
import natsort
import shutil
import operator
import webbrowser
from conllu import parse
from conllu import parse_tree
import pyconll as pc
from ast import literal_eval
from itertools import tee, islice, chain


# Input dirs
dir_FN_annotated = 'framenet_annotated'
dir_TP_annotated = 'grew_annotated'

# Output dir for conllu
dir_output = 'out_fm'
shutil.rmtree(dir_output, ignore_errors=True)
os.makedirs(dir_output)

# Output dir for xml
dir_output_xml = 'out_xml'
shutil.rmtree(dir_output_xml, ignore_errors=True)
os.makedirs(dir_output_xml)

"""
# Output dir for svg
dir_svg = 'svg_fm'
shutil.rmtree(dir_svg, ignore_errors=True, onerror=None)
os.makedirs(dir_svg)

# Output dir for html
dir_html = 'template_fm'
shutil.rmtree(dir_html, ignore_errors=True, onerror=None)
os.makedirs(dir_html)
"""


# Given a string composed of one or several tokens and a sentence
# Returns the ordered list of ids of the tokens in the sentence
def search_id(toks, sent):

    toks = re.sub('& quot ;', '&quot;', toks)
    toks_list = toks.split(' ')
    lines = sent.split('\n')
    ids = list()

    # Keeping the ids of every matched line for every token
    for token in toks_list:
        for line in lines:
            if len(line)>1 and token == line.split('\t')[1]:
                ids.append(line.split('\t')[0])

    # When there are more matched ids than tokens to matchs
    if len(ids) > len(toks_list):

        # Creating a new list (by value, not reference) for not losing elements in the iteration for deleting
        ids_copy = ids[:]

        n_matches = 1
        n_searching = 0
        sig = ""

        ids_iter = iter(ids_copy)

        for x in ids_iter:

            # When all tokens have been correctly matched
            if n_matches == len(toks_list):

                # Keeping the matched tokens
                until = n_matches-1
                ids = ids[:until]
                ids.append(sig)
                break

            # Calculating and searching the next id to match
            sig = str(int(x) + 1)

            # Deleting the current element if the next one is not in the rest of the list
            if sig not in ids[1:]:
                ids.remove(x)

            # If the next id to match is in the list
            else:
                # Keeping the elements until the current element and from the next matched id
                n_x = ids.index(x)
                n_sig = ids.index(sig)
                ids = ids[:n_x + 1] + ids[n_sig:]
                # Skipping the removed elements in the iteration
                n_to_skip = n_sig - n_x - 1
                for n in range(n_to_skip):
                    next(ids_iter)

                n_matches += 1

            if len(ids) == len(toks_list):
                break

            n_searching += 1

    return ids


# Given a list of features and a sentence
# Returns the subtree composed of the tokens of the sentence with a "yes" value in the features selected
def keep_annotations(anns, sent):

    lines = sent.split('\n')
    main = ""
    new_root = False

    # Solving the problem of sentences whose main clause does not include root
    for line in lines:
        line_fields = line.split('\t')

        # Getting the root when not in main theme or rheme
        if len(line_fields) >= 5 and "t=no" in line_fields[5] and "r=no" in line_fields[5]:
            new_root = True

    # When the original sentence root is not included in the compressed sentence
    if new_root:

        # Getting the conllu parsed version of the sentence
        try:
            sentences = parse(sent)
        except pc.exception.ParseError:
            sentences = parse(to_conllu(sent))
        sentence = sentences[0]

        # Getting the immediate sons of the head of the original root
        found = False
        hijos = [sentence.to_tree()]

        # While the head of the main clause hasn't been found
        while not found and len(hijos) > 0:
            for hijo in hijos:

                # Explore the tree until finding a t=yes or r=yes annotated node (the head of the main clause necessary)
                for ann in anns:
                    if hijo.token['feats'][ann] == 'yes':
                        hijo.token['deprel'] = 'root'
                        hijo.token['head'] = 0
                        found = True
                        break

            # Searching in the sons of every son in case immediate sons aren't the head of the selected main clause
            nietos = []
            for hijo in hijos:
                nietos.extend(hijo.children)
            hijos = nietos

        # Updating lines with the new root token annotated as such
        lines = sentence.serialize().split('\n')

    # Keeping only the lines corresponding to the main theme and rheme of the sentence
    for line in lines:
        line_fields = line.split('\t')

        if len(line_fields)>=5 and ("t=yes" in line_fields[5] or "r=yes" in line_fields[5]):
            main += line + '\n'

    return main


# Given a sentence
# Returns a tuple with the tokens composing its theme and its rheme
def forms_theme_rheme(sent):

    lines = sent.split('\n')
    theme = ""
    rheme = ""

    for line in lines:
        line_fields = line.split('\t')
        if len(line_fields)>=5 and ("t=yes" in line_fields[5]):
            theme += line_fields[1] + ' '
        if len(line_fields)>=5 and ("r=yes" in line_fields[5]):
            rheme += line_fields[1] + ' '

    return (theme, rheme)


# Given a sentence
# Returns a tuple with the PoS of the tokens composing its theme and its rheme
def pos_theme_rheme(sent):

    lines = sent.split('\n')
    theme_pos_list = list()
    rheme_pos_list = list()

    for line in lines:
        line_fields = line.split('\t')
        if len(line_fields)>=5 and ("t=yes" in line_fields[5]):
            theme_pos_list.append(line_fields[3])
        if len(line_fields)>=5 and ("r=yes" in line_fields[5]):
            rheme_pos_list.append(line_fields[3])

    return (theme_pos_list, rheme_pos_list)


# Given a sentence
# Returns the list of the forms of the verbs contained in the main proposition
def get_main_verb_forms(sent):

    lines = sent.split('\n')
    main_verb_forms = list()

    for line in lines:
        line_fields = line.split('\t')
        if len(line_fields)>=5 and ("m=yes" in line_fields[5]) and (line_fields[3][0] == 'v'):
            main_verb_forms.append(line_fields[1])
    return main_verb_forms


# Given a sentence
# Returns a tuple with a boolean True value if a reported speech subject if annotated and its string; or a boolean False value and an empty string otherwise
def get_modalitySpeaker(sent):

    lines = sent.split('\n')
    modality_speaker = ""
    found = False

    for line in lines:
        line_fields = line.split('\t')
        if len(line_fields)>=5 and ("rep=yes" in line_fields[5]):
            found = True
            modality_speaker += line_fields[1] + ' '

    return (found, modality_speaker)


# Given a sentence
# Returns a tuple with the lists with the ids of the elements of its theme and rheme
def ids_theme_rheme(sent):

    lines = sent.split('\n')
    theme = list()
    rheme = list()

    for line in lines:
        line_fields = line.split('\t')
        if len(line_fields)>=5 and ("t=yes" in line_fields[5]):
            theme.append(line_fields[0])
        if len(line_fields)>=5 and ("r=yes" in line_fields[5]):
            rheme.append(line_fields[0])
    return (theme, rheme)


# Reindexing the tokens of a sentence to avoid gaps in order to match continuous annotations along them
def reset_ids(sent):
    sent_lines = sent.split('\n')

    # Beggining ids from 1
    id_new = 1

    # Creating a tmp file with both new a original ids
    tmp = ""

    # Keeping previous and new ids with the format new_id-prev_id
    for line in sent_lines:
        if len(line) > 1:
            tmp += str(id_new) + '-' + line + '\n'
            id_new += 1

    # Creating the file for the resetted ids
    resetted = sent

    # Getting the original id
    for line_tmp in tmp.split('\n'):
        if len(line_tmp) > 1:
            id_old = re.search('-(.+)', line_tmp.split('\t')[0]).group(1)
            id_new = re.search('(.+)-', line_tmp.split('\t')[0]).group(1)

            # Resetted is rewritten for every pair id_old / id_new
            lines_resetted = resetted.split('\n')
            resetted = ""

            for line_resetted in lines_resetted:
                if len(line_resetted) > 1 and line_resetted.split('\t')[6] == id_old:
                    line_modified = re.sub(id_old + r'(.+?)', str(id_new) + r'\1', line_resetted)
                elif len(line_resetted) > 1 and line_resetted.split('\t')[0] == id_old:
                    line_modified = re.sub(r'^' + id_old + '(.+?)', str(id_new) + r'\1', line_resetted)
                else:
                    line_modified = line_resetted

                if (len(line_modified)>1):
                    resetted += line_modified + '\n'


    return resetted


def to_conllu(sentence):
    lines = sentence.split('\n')
    ok = ""
    for l in lines:
        if len(l) > 1:
            line_ok = l[:-1] + '\t_\t_\n'
            ok += line_ok
        else:
            ok += (l + '\n')
    return ok



# Transforms a conllu sentence into the string with its forms
def txt_transformer(file_conllu):
    s_list = list()
    with open(file_conllu, 'r') as f:
        conll = pc.load_from_string(f.read())
    for s in conll:
        s_txt = ""
        for word in s[:-1]:
            s_txt = s_txt + " " + word.form
        s_txt = s_txt + ".\n"
        s_list.append(s_txt)
    return s_list



# Transforms a conllu sentence into the string with its forms
def txt_transformer_str(sentence):
    try:
        conll = pc.load_from_string(sentence)
    except pc.exception.ParseError:
        conll = pc.load_from_string(to_conllu(sentence))
    sent = conll[0]
    s_txt = ""
    for word in sent:
        s_txt = s_txt + " " + word.form
    s_txt = s_txt + ".\n"
    return s_txt


# Takes the id of a token as the first argument,
# the id of another token as the second argument
# a dependency relation type as the third argument and
# a sentence as the fourth argument
# returning the rewriten sentence with the second token depending on the first one
def rewrite_dep(head_id, dep_id, arg, sentence):

    for token in sentence[0]:
        if token['id'] == int(dep_id):
            token['head'] = head_id
            token['deprel'] = arg

    # print(head_id, dep_id, arg, sentence[0].serialize())
    return sentence[0].serialize()


# Returns a file name without the extension
def remove_ext(filename):
    return filename[:filename.rfind(".")]


# Getting the list of ids of the sons of
# the id corresponding to the first argument
# in the sentence corresponding to the second argument
def get_sons_ids(id, sent):
    try:
        sentences = parse(sent)
    except pc.exception.ParseError:
        sentences = parse(to_conllu(sent))
    sentence = sentences[0]

    ids = [id]
    ids_sons = list()
    hijos = [sentence.to_tree()]

    while len(hijos) > 0:
        for hijo in hijos:
            if str(hijo.token['head']) in ids:
                ids_sons.append(hijo.token['id'])
                ids.append(str(hijo.token['id']))
                deps = hijo.children
                for dep in deps:
                    ids.append(str(dep.token['id']))

        # Searching in the sons of every son in case immediate sons aren't the head of the selected main clause
        nietos = []
        for hijo in hijos:
            nietos.extend(hijo.children)
        hijos = nietos

    # print(sentence.serialize())
    # print(id, ids_sons)
    return ids_sons


def coord_to_sentence(sent):

    heads = list()

    try:
        sentences = parse(sent)
    except pc.exception.ParseError:
        sentences = parse(to_conllu(sent))
    sentence = sentences[0]

    while "coord_fixed" in sentence.serialize():
        # print(file_grew)
        hijos = [sentence.to_tree()]
        found = False

        # Getting the head token of a coord_fixed dependency
        while len(hijos) > 0 and not(found):
            for hijo in hijos:
                print(hijo.token['form'])
                deps = hijo.children

                # Explore the tree until finding a coord_fixed dependency
                for dep in deps:
                    if dep.token['deprel'] == 'coord_fixed':
                        dep.token['deprel'] = 'coord_separated'

                        # Getting the node which is head of the coordinated dependencies
                        heads.append(hijo)
                        found = True
                        break

            # Searching in the sons of every son in case immediate sons aren't the head of the selected main clause
            nietos = []
            for hijo in hijos:
                nietos.extend(hijo.children)
            hijos = nietos

    sentences_no_coord = list()
    id_dep_to_separate = list()

    # If a coordination to be fixed has been found
    if len(heads) > 0:
        for head in heads:

            # Choosing the most frequent dependency type (except for punct) of the head of the coordination
            """
            # Creating a dictionary with the frequencies of dependencies from the head node of the coordination
            freq = dict()
            list_deps_coord = [h.token['deprel'] for h in head.children]
            for dep_coord in list_deps_coord:
                if dep_coord != 'punct':
                    if dep_coord in freq:
                        freq[dep_coord] += 1
                    else:
                        freq[dep_coord] = 1
                        
            id_head_to_separate = head.token['id']
            dep_to_separate = max(freq.items(), key=operator.itemgetter(1))[0]
            id_dep_to_separate.append((id_head_to_separate, dep_to_separate, freq[dep_to_separate]))
            """

            id_head_to_separate = head.token['id']

            for d in head.children:
                # print(d.token['form'])
                if d.token['feats']['c'] == "yes":
                    dep_to_separate = d.token['deprel']
                    break

            # print('Coordinated depedency: ', dep_to_separate)

            # Keeping the frequency of the dependency chosen in order to avoid conjunction removal when more than two coordinates are involved
            id_dep_to_separate.append((id_head_to_separate, dep_to_separate))


    # Obtaining list of subtrees depeding on the head of the coordinate clauses as the chosen dependency
    sent_lines = sentence.serialize().split('\n')

    for rewr in id_dep_to_separate:
        ids_to_maintain = list()

        # Getting the id of the dependent
        for l in sent_lines:
            if len(l.split('\t')) > 1 and int(l.split('\t')[6]) == int(rewr[0]) and l.split('\t')[7] == rewr[1] and "c=yes" in l.split('\t')[5]:
                ids_to_maintain.append(l.split('\t')[0])

        # n_ids_to_maintain = 0
        for id_to_maintain in ids_to_maintain:
            # n_ids_to_maintain += 1

            # Getting the ids of the rest of coordinates' heads
            ids_to_delete = list()
            for id in ids_to_maintain:
                if id != id_to_maintain:
                    ids_to_delete.append(id)
            # print(ids_to_delete)
            # Obtaining the subtree immediately containing the coordinate
            dependents_ids_list_maintain = get_sons_ids(str(id_to_maintain), sentence.serialize())
            dependents_ids_list_maintain.append(int(id_to_maintain))

            # Obtaining the subtrees of the rest of the coordinates
            dependents_ids_list_delete = list()
            for id_del in ids_to_delete:
                dependents_ids_list_delete.extend(get_sons_ids(str(id_del), sentence.serialize()))
                dependents_ids_list_delete.append(int(id_del))



            # print("Keep: ", dependents_ids_list_maintain)   # Unnecessary now
            # print("Delete: ", dependents_ids_list_delete)

            main = ""

            # Getting the id of the conjuntion
            for line in sent_lines:
                if len(line.split('\t')) > 1 and int(line.split('\t')[6]) == rewr[0] and line.split('\t')[7] == "coord_separated":
                    id_conj = int(line.split('\t')[0])
                    break


                # For those lines not depending on the head of the coordination
                # not being conjunctions depending on the head of the coordination when there are more than two coordinates
                # not being punctuation depending on the conjunction
            for line in sent_lines:
                if len(line) > 1 and int(line.split('\t')[0]) not in dependents_ids_list_delete and (
                        not (int(line.split('\t')[6]) == rewr[0] and line.split('\t')[7] == "coord_separated")) and (
                        not (int(line.split('\t')[6]) == id_conj and line.split('\t')[7] == "punct")):
                    # Dealing with conjuctions and punctuation in coordination when only one coordinate is deleted (keeping the when there are more than two coordinates but deleting them when the removed coordinate is the last one)
                    # not (int(line.split('\t')[6]) == rewr[0] and line.split('\t')[7] == "coord_separated" and rewr[2] <= 2)) and (
                    # not (int(line.split('\t')[6]) == rewr[0] and line.split('\t')[7] == "coord_separated" and rewr[2] > 2 and n_ids_to_maintain == len(ids_to_maintain))) and (
                    # not (int(line.split('\t')[6]) == rewr[0] and line.split('\t')[7] == "punct" and rewr[2] <= 3)):
                    main += line + '\n'

            sentences_no_coord.append(main)


    # print(sentence.serialize())
    # print(id_dep_to_separate)
    # print("\n".join(sentences_no_coord))
    # print("___________________________________________________________________________________")
    return "\n".join(sentences_no_coord)



"""
def compress(list_ids, sent):

    # Cleaning repeated empty lines in the sentence
    while True:
        sent_clean = re.sub('\n\n', '\n', sent)
        if sent_clean == sent:
            break
        sent = sent_clean

    sent_lines = sent.split('\n')
    sent_compressed = ""

    # First token position
    id_first = int(list_ids[0])

    # Las token position
    id_last = int(list_ids[-1])

    # Getting the line of the first token of the ids list and its form
    line_first_from_form = '\t'.join(sent_lines[id_first].split('\t')[2:])
    token_compressed = sent_lines[id_first].split('\t')[1]

    for line in sent_lines[:id_first]:
        if len(line) > 1:
            sent_compressed += line + '\n'

    for line in sent_lines[(id_first + 1):(id_last + 1)]:
        if len(line) > 1:
            token_compressed += '__' + line.split('\t')[1]

    sent_compressed += str(id_first + 1) + '\t' + token_compressed + '\t' + line_first_from_form + '\n'

    for line in sent_lines[(id_last + 1):]:
        sent_compressed += line + '\n'

    return sent_compressed
"""

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)



# List of FrameNet annotations (one list element per sentence)
FN_annotated_list = list()

## Data structure:
# - Every FrameNet annotation consist of a Python dictionary with
# Key: a Python tuple (type of frame, head string)
# Value: list of arguments
# - Every argument is a Python tuple (type of FrameNet relation, string)


## Creating a XML file with the theme/rheme and the FrameNet annotations information

# XML content to save for the text
xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>

<!DOCTYPE text [
	<!ELEMENT text (sentence+)>
	    <!ATTLIST text id CDATA #REQUIRED>
	<!ELEMENT sentence (theme, rheme, semantic_roles)>
		<!ELEMENT theme (token*)>
		<!ELEMENT rheme (token*)>
		<!ELEMENT token (#PCDATA)>
		    <!ATTLIST token pos CDATA #REQUIRED>
		<!ELEMENT semantic_roles (frame*)>
		<!ELEMENT frame (argument*)>
            <!ATTLIST frame type CDATA #REQUIRED>
            <!ATTLIST frame head CDATA #REQUIRED>
		<!ELEMENT argument EMPTY>
            <!ATTLIST argument type CDATA #REQUIRED>
            <!ATTLIST argument dependent CDATA #REQUIRED>
]>


'''


# Getting the ordered list with the FrameNet annotations for every sentence
files_fm = natsort.natsorted(os.listdir(dir_FN_annotated))
for file in files_fm:
    with open(dir_FN_annotated + '/' + file, 'r') as f:
        dict_ann = literal_eval(f.read())
        FN_annotated_list.append(dict_ann)


n_sentence = 0
files_grew = natsort.natsorted(os.listdir(dir_TP_annotated))
for file_grew in files_grew:
    with open(dir_TP_annotated + '/' + file_grew) as f:
        sentences = parse(f.read())
        xml_sentence = xml + '<text id="' + remove_ext(file_grew) + '">\n\n\n'


        # --> String representation of the conllu structure of the sentences in a text
        fm_annotated = ""

        for sentence in sentences:

            # Keeping the reporter modality marker before transforming the original sentence
            reporter = get_modalitySpeaker(sentence.serialize())

            # Reducing every sentence to the theme + rheme of the main clause
            sentence_main = keep_annotations(['t', 'r'], sentence.serialize())

            # Cleaning repeated empty lines in the sentence
            while True:
                sent_clean = re.sub('\n\n', '\n', sentence_main)
                if sent_clean == sentence_main:
                    break
                sentence_main = sent_clean

            # Rewriting the ids: beginning from 1 and with no gaps
            sentence_main = reset_ids(sentence_main)

            # Cleaning repeated empty lines in the sentence
            while True:
                sent_clean = re.sub('\n\n', '\n', sentence_main)
                if sent_clean == sentence_main:
                    break
                sentence_main = sent_clean

            # Coordination module off
            """
            if len(sentence_main) > 1:
                # Apparently fails (infinite loop) when "coord_fixed" is near the root
                # Transforming every coordinate to a sentence
                sentence_main_coords = coord_to_sentence(sentence_main)
            else:
                print("No se ha podido extraer el tema y el rema de la oración", txt_transformer_str(sentence.serialize()))
            """

            fm_anns = FN_annotated_list[n_sentence]
            n_sentence += 1

            # print('________________________________________________________')
            # print(sentence_main)

            xml_sentence += '\t<sentence>\n'

            tokens_theme = forms_theme_rheme(sentence_main)[0].split()
            tokens_rheme = forms_theme_rheme(sentence_main)[1].split()
            pos_theme = pos_theme_rheme(sentence_main)[0]
            pos_rheme = pos_theme_rheme(sentence_main)[1]
            pos_rheme = pos_theme_rheme(sentence_main)[1]
            tokens_pos_theme = zip(tokens_theme, pos_theme)
            tokens_pos_rheme = zip(tokens_rheme, pos_rheme)

            verbs = get_main_verb_forms(sentence_main)

            xml_sentence += '\t\t<theme>\n\t\t\t'
            for token_pos in tokens_pos_theme:
                xml_sentence += '<token pos="' + token_pos[1] + '">' + token_pos[0] + '</token>'
            xml_sentence += '\n\t\t</theme>\n'

            xml_sentence += '\t\t<rheme>\n\t\t\t'
            for token_pos in tokens_pos_rheme:
                xml_sentence += '<token pos="' + token_pos[1] + '">' + token_pos[0] + '</token>'
            xml_sentence += '\n\t\t</rheme>\n'

            xml_sentence += '\t\t<semantic_roles>\n'

            if reporter[0]:
                xml_sentence += '\t\t\t<frame type="Modality_Reporter" head="' + reporter[1] + '"></frame>\n'

            # Getting the ids of the tokens conforming the head of a FrameNet frame
            for frame_head in fm_anns:

                # --> FrameNet frame
                frame = frame_head[0]

                # --> Tokens representing the head of the arguments
                frame_tokens = frame_head[1]

                # --> List of the ids (ordered) of the tokens corresponding to the head of the arguments
                h_ids = search_id(frame_tokens, sentence_main)

                print(verbs)

                for verb in verbs:
                    if verb in frame_tokens:

                        xml_sentence += '\t\t\t<frame type="' + frame + '" head="' + frame_tokens + '">'

                        for dep_ann in fm_anns[frame_head]:

                            # --> The type of argument
                            argument_type = dep_ann[0]

                            # --> The tokens representing the argument
                            argument_tokens = dep_ann[1]

                            # --> List of the ids (ordered) of the tokens correponding to the argument
                            h_dep_ids = search_id(argument_tokens, sentence_main)
                            # print(argument_tokens, h_dep_ids, '\n' + sentence_main)

                            # sentence_main_compressed = compress(h_dep_ids, sentence_main)

                            """
                            # Making the tokens of a dependency depend on its first token
                            for h_dep_id in h_dep_ids[1:]:
                                sentence_main = rewrite_dep(h_dep_ids[0], h_dep_id, argument_type, parse(sentence_main))
                            """

                            xml_sentence += '\n\t\t\t\t<argument type="' + argument_type + '" dependent="' + argument_tokens + '"/>'
                        xml_sentence += '</frame>\n'
            xml_sentence += '\t\t</semantic_roles>\n'
            xml_sentence += '\t</sentence>\n\n\n'

            fm_annotated += (sentence_main + '\n')


        # Creating a new file with the selected subtree with the FrameNet annotations
        with open(dir_output + '/' + file_grew, "w") as h:
            lines = fm_annotated.split('\n')
            ok = ""
            for l in lines:
                if len(l) > 1:
                    line_ok = l[:-1] + '\t_\t_\n'
                    ok += line_ok
                else:
                    ok += (l + '\n')
            h.write(ok)
            h.close()

        xml_sentence += '</text>'
        xml_sentence = re.sub(" & quot ;", "", xml_sentence)
        xml_sentence = re.sub(" & quot;", "", xml_sentence)
        xml_sentence = re.sub(" &quot;", "", xml_sentence)
        xml_sentence = re.sub(" , ", ", ", xml_sentence)

        with open(dir_output_xml + '/' + remove_ext(file_grew) + '.xml', "w") as xml_file:
            xml_file.write(xml_sentence)
            xml_file.close()
























'''

## Obtaing SVG trees from conllu annotations

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
'''
