from utils import order_graphs, disorder_graphs, to_conllu, annotator_recursive
from conllu import parse
import pyconll as pc
import grew
import os
import shutil
import webbrowser
import re

# Install Grew and its requirements, and the Grew package must be loaded for the project. Installation nstructions can be found here: http://grew.fr/install/
# conll must also be installed (via pip for example) and the package must be loaded for the project
# Module working with Python 3.8 interpreter and PyCharm 2020.1 version


## Start Grew tool after importing the library
grew.init()


## Loading a Grew grs (Graph Rewriting System)
# Documentation can be found here: http://grew.fr/grs/
# More information on rules (embedded in GRS) can be found here: http://grew.fr/rule/
# More information on commands (embedded in rules) can be found here: http://grew.fr/commands/


## Directories paths

# Input directory
# dir_original = 'in/AnCora_Surface_Syntax_Dependencies/conllu'
dir_original = 'in_short'

# Output directory
# Deleting previous output directory (subfolder creation inside loop)
dir_output = 'out'
shutil.rmtree(dir_output, ignore_errors=True)
os.makedirs(dir_output)

# Temporary file with the text of each sentence
tmp_file = 'out/tmp_sentence.txt'

# SVG directory
# Deleting previous output SVG directory (subfolder creation inside loop)
dir_svg = 'svg'
shutil.rmtree(dir_svg, ignore_errors=True, onerror=None)
os.makedirs(dir_svg)

# HTML directory
# Deleting previous output HTML directory
dir_html = 'templates'
shutil.rmtree(dir_html, ignore_errors=True)
os.makedirs(dir_html)

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

# Workaround for copying directories
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

## Creating different simpler subgrammars (in order to avoid GrewError: 'More than 10000 rewriting steps: ckeck for loops or increase max_rules value')
grs_list = list()


grs_solving_weirdAnn = """

rule cobj_subordination {
  pattern {
    R -[cobj]-> A;
    R -[cobj]-> B;
    A << B;
  }
  commands {
    del_edge R -[cobj]-> B;
    add_edge A -[cobj]-> B;
  }
}

strat S1 { Onf ( cobj_subordination ) }
"""


grs_main = """

rule subordinate_dobj_clause {
  pattern {
    N0 -[nsubj]-> S;
    N0 -[dobj]-> N1;
    N1 -[cobj]-> N2;
  }
  commands {
    S.rep=yes;
    S.recursive=yes;
    N2.main=yes;
    N2.recursive=yes;
  }
}

rule main_root {
  pattern {
    X -[root]-> R;
  }
  commands {
    R.main=yes;
    R.recursive=yes;
  }
}

strat S1 { Try ( If ( subordinate_dobj_clause, Iter ( subordinate_dobj_clause ), main_root ) ) }
"""


grs_nsubj_ellision_rep = """

rule nsubj_ellision_rep {
  pattern {
    N0 -[nsubj]-> S;
    N0 -[dobj]-> N1;
    N1 -[cobj]-> N2;
  }
  without {
    N2 -[nsubj]-> S2
  }
  commands {
    del_edge N0 -[nsubj]-> S;
    add_edge N2 -[nsubj]-> S;
    N2.main=yes;
    N2.recursive=yes;
  }
}

strat S1 { Onf ( nsubj_ellision_rep ) }
"""


grs_preceding_subjects = """

rule preceding_subject {
  pattern {
    R [ main="yes" ];
    S [ main="yes" ];
    R -[nsubj]-> S;
    S << R;
  }
  commands {
    S.theme=yes;
    S.recursive=yes;
  }
}

strat S1 { Try ( Iter ( preceding_subject ) ) }
"""


grs_preceding_subject_first = """

rule preceding_subject_first {
  pattern {
    R1 [ theme="no" ];
    T1 [ theme="yes" ];
    R1 -> T1;
    R2 [ theme="no" ];
    T2 [ theme="yes" ];
    R2 -> T2;
    T1 << T2;
  }
  commands {
    T2.theme=no;
    T2.recursive=yes;
  }
}

strat S1 { Try ( Iter ( preceding_subject_first ) ) }
"""


grs_dealingWith_coordination = """

rule coordinated {
  pattern {
    X -[root]-> X;
    X -[coord]-> R1;
    X -[coord]-> R2;
    R1 << R2;
  }
  commands {
    R2.main=no;
    R2.recursive=yes;
  }
}

strat S1 { Try ( Iter ( coordinated ) ) }
"""


grs_main_satellites_out = """

rule ignore_satellites {
  pattern {
    R [ main="yes" ];
    R -[ advmod|advcl|prepv|prep|cc ]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}

strat S1 { Try ( Iter ( ignore_satellites ) ) }
"""


grs_main_extra_in = """

rule ignore_only_preps_satellites {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[prep|prepv]-> C;
  }
  without {
    R -[dobj]-> *;
  }
  commands {
    C.main=yes;
    C.recursive=yes;
  }
}

strat S1 { Try ( Iter ( ignore_only_preps_satellites ) ) }
"""


grs_main_extra_in_sub = """

rule ignore_only_preps_satellites_sub {
  pattern {
    X -[^root]-> R;
    R [ main="yes" ];
    R -[prep|prepv]-> C;
  }
  without {
    R -[dobj]-> *;
  }
  commands {
    C.main=yes;
    C.recursive=yes;
  }
}

strat S1 { Try ( Iter ( ignore_only_preps_satellites_sub ) ) }
"""


grs_rheme_head = """

rule rheme {
  pattern {
    T [ theme="yes" ];
    V -> T;
    V [ theme="no", main="yes" ];
    C [ main=yes, theme="no" ];
    V -[^advcl|advmod]-> C;
    T << C;
  }
  commands {
    V.rheme=yes;
    C.rheme=yes;
    C.recursive=yes;
  }
}

strat S1 { Iter ( Try ( rheme ) ) }
"""


grs_rheme_cleaning = """
rule rheme_not_rcmod {
  pattern {
    R [ rheme="yes" ];
    R -[rcmod]-> C;
  }
  commands {
    C.rheme="no";
    C.recursive=yes;
  }
}

rule rheme_not_punct {
  pattern {
    R [ rheme="yes" ];
    R -[punct]-> C;
  }
  commands {
    C.rheme=no;
    C.recursive=yes;
  }
}

strat S1 { Try ( Iter ( Alt ( rheme_not_rcmod, rheme_not_punct ) ) ) }
"""


grs_rep = """

rule annotated_reported_ellided_nsubj {
  pattern {
    V -[nsubj]-> S;
    X -[cobj]-> V;
  }
  commands {
    S.rep=yes;
    S.recursive=yes;
  }
}

rule annotated_reported_advcl {
  pattern {
    X -[advcl]-> R;
    R -[cobj]-> O;
    O -[nsubj]-> S;
    R [ form="según"];
  }
  commands {
    S.rep=yes;
    S.recursive=yes;
  }
}

rule annotated_reported_advcl_bareN {
  pattern {
    X -[advcl]-> R;
    R -[pobj]-> S;
    R [ form="según"];
  }
  commands {
    S.rep=yes;
    S.recursive=yes;
  }
}

rule annotated_reported_advcl_weirdAnn {
  pattern {
    X -[advcl]-> R;
    R -[cobj]-> O;
    O -[cobj]-> S;
    O << S;
    R [ form="según"];
  }
  commands {
    S.rep=yes;
    S.recursive=yes;
  }
}

strat S1 { Try ( Iter ( Alt ( annotated_reported_ellided_nsubj, annotated_reported_advcl, annotated_reported_advcl_bareN, annotated_reported_advcl_weirdAnn ) ) ) }
"""


# Ordering matters:
# the features generated by the previous rule strategies are available for the subsequent ones no matter the strategies defined
grs_list.append(grs_solving_weirdAnn)
grs_list.append(grs_main)
grs_list.append(grs_nsubj_ellision_rep)
grs_list.append(grs_preceding_subjects)
grs_list.append(grs_preceding_subject_first)
grs_list.append(grs_dealingWith_coordination)
grs_list.append(grs_main_satellites_out)
grs_list.append(grs_main_extra_in)
grs_list.append(grs_main_extra_in_sub)
grs_list.append(grs_rheme_head)
grs_list.append(grs_rheme_cleaning)
grs_list.append(grs_rep)



for grs in grs_list:
    gram = grew.grs(grs)

n_gram = 0
n_exceptions = 0
n_processed = 0

for grs in grs_list:

    gram = grew.grs(grs)

    # Taking original corpus as input for the fist iteration and the output of the previous iterations for subsequent iterations
    n_gram += 1
    if n_gram == 1:
        dir_input = dir_original
    else:
        os.remove(tmp_file)
        dir_input = dir_output
    entrada = os.listdir(dir_input)


    ## Transforming a conllu file into a list of the strings of its sentences

    # Obtaining file names (different ways for the first and subsequent iterations in case not all texts from the corpus are analyzed)
    if n_gram == 1:

        for file in entrada:
            # print(str(n_gram) + ' ' + file)
            if file.endswith(".conllu"):
                f_noExt = file[:-7]
                os.makedirs(dir_output + '/' + f_noExt)

            input = open(dir_input + '/' + file, "r", encoding="utf-8")
            sentences = parse(input.read())
            input.close()
            graphs = list()

            # Appending every sentence to the graph list object
            for sentence in sentences:
                tmp_nf = open(tmp_file, 'w')
                tmp_nf.write(sentence.serialize())
                tmp_nf.close()
                graph = grew.graph(tmp_file)
                graphs.append(graph)

            ## Transforming the Graph object into an ordered one in order to use preceding constrains in rules
            ordered_graphs = order_graphs(graphs)
            output_graphs = list()

            # Appending the unordered output of the GRS application to every ordered Grew graph sentence
            for g in ordered_graphs:
                try:
                    output_graphs.extend(grew.run(gram, g, "S1"))
                    n_processed += 1
                except grew.utils.GrewError:
                    output_graphs.extend([g])
                    n_exceptions += 1
            unordered_graphs = disorder_graphs(output_graphs)

            ruta = dir_output + '/' + f_noExt + '/'
            with open(ruta + f_noExt + '_annotated.conllu', "w") as output:
                for e in unordered_graphs:
                    output.write(to_conllu(e) + '\n')

            # Recursive subtree annotation for recursive=yes featured nodes
            with open(ruta + f_noExt + '_annotated_recursive.conllu', "w") as output:
                output.write(annotator_recursive(dir_output + '/' + f_noExt + '/' + f_noExt + '_annotated.conllu') + '\n')


    else:

        dir_output_files = os.listdir(dir_output)
        for file in entrada:
            # print(str(n_gram) + ' ' + file)
            f_noExt = file

            input = open(dir_input + '/' + file + '/' + file + '_annotated_recursive.conllu', "r", encoding="utf-8")
            sentences = parse(input.read())
            input.close()
            graphs = list()

            # Appending every sentence to the graph list object
            for sentence in sentences:
                tmp_nf = open(tmp_file, 'w')
                content = sentence.serialize()
                sentence_lines = content.split('\n')
                ok = ""
                for l in sentence_lines:
                    if len(l) > 1:
                        line_ok = l + '\t_\t_\n'
                        ok += line_ok
                tmp_nf.write(ok)
                tmp_nf.close()

                graph = grew.graph(tmp_file)
                graphs.append(graph)


            ## Transforming the Graph object into an ordered one in order to use preceding constrains in rules
            ordered_graphs = order_graphs(graphs)
            output_graphs = list()

            ruta = dir_output + '/' + f_noExt + '/'
            with open(ruta + f_noExt + '_annotated.conllu', "w") as output:
                for e in unordered_graphs:
                    output.write(to_conllu(e) + '\n')

            # Recursive subtree annotation for recursive=yes featured nodes
            with open(ruta + f_noExt + '_annotated_recursive.conllu', "w") as output:
                output.write(
                    annotator_recursive(dir_output + '/' + f_noExt + '/' + f_noExt + '_annotated.conllu') + '\n')

            # Appending the unordered output of the GRS application to every ordered Grew graph sentence
            for g in ordered_graphs:
                try:
                    output_graphs.extend(grew.run(gram, g, "S1"))
                    n_processed += 1
                except grew.utils.GrewError:
                    output_graphs.extend([g])
                    n_exceptions += 1

            unordered_graphs = disorder_graphs(output_graphs)

            ruta = dir_output + '/' + f_noExt + '/'
            with open(ruta + f_noExt + '_annotated.conllu', "w") as output:
                for e in unordered_graphs:
                    output.write(to_conllu(e) + '\n')

            # Recursive subtree annotation for recursive=yes featured nodes
            with open(ruta + f_noExt + '_annotated_recursive.conllu', "w") as output:
                output.write(annotator_recursive(dir_output + '/' + f_noExt + '/' + f_noExt + '_annotated.conllu') + '\n')

print('Numero de estrategias aplicadas correctamente: ' + str(n_processed))
print('Numero de estrategias erróneas: ' + str(n_exceptions))
os.remove(tmp_file)


## Creating one folder for every text containing the SVG files os their sentences trees:
# - the original,
# - the rewriten one and
# - the rewriten one containing additional features)

# For relative commands execution
os.chdir("/home/elena/PycharmProjects/TP_grammar/venv/main")

nombres_textos = os.listdir(dir_output)

for nombre in nombres_textos:

    os.makedirs(dir_svg + '/' + nombre)
    ruta_input = 'out/' + nombre + '/' + nombre + '_annotated_recursive.conllu'

    # Deleting unnecessary features
    with open(ruta_input, 'r+') as f:
        raw = f.read()
        raw = re.sub('\|main=','|m=', raw)
        raw = re.sub('\|theme=','|t=', raw)
        raw = re.sub('\|rheme=','|r=', raw)
        raw = re.sub('recursive=(yes|no)\|','', raw)
        f.close()
    with open(ruta_input, 'w') as f:
        f.write(raw)

    comando_gen_rewriten_complete = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '_rewriten_complete.svg -c ' + ruta_input + ' --ignore-double-indices --feats'
    os.system(comando_gen_rewriten_complete)

    # comando_gen_original = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '.svg -c in/AnCora_Surface_Syntax_Dependencies/conllu/' + nombre + '.conllu --ignore-double-indices'
    # comando_gen_rewriten = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '_rewriten.svg -c out/' + nombre + '/' + nombre + '_annotated_recursive.conllu --ignore-double-indices'
    # os.system(comando_gen_original)
    # os.system(comando_gen_rewriten)

# Creating folders for both left and right trees in order to visualy compare, mainly:
# - Overlapping annotations
# - Subordinate annotations (that depends on another previous annotation)

for d in os.listdir(dir_svg):
    os.makedirs(dir_svg + '/' + d + '_right')
    copytree(dir_svg + '/' + d, dir_svg + '/' + d + '_right')
    os.rename(dir_svg + '/' + d, dir_svg + '/' + d + '_left')


## Colouring in background green nodes corresponding to main clauses

# Creating the dictionary of annotation types and the corresponding color for the ellipses containing that feature
# colors_right = {'main': '#98D2A5', 'theme': '#BEDA48'}            # Testing more than one
# colors_left = {'main': '#98D2A5'}                                 # Definitive
# colors_right = {'theme': '#BEDA48', 'rheme': '#DA8D48'}           # Definitive

colors_left = {'m': '#98D2A5'}
colors_right = {'t': '#BEDA48', 'r': '#DA79E8'}

# Selecting the SVG files to color
for nombre in nombres_textos:
    outputdir_img_left = dir_svg + '/' + nombre + '_left'
    outputdir_img_right = dir_svg + '/' + nombre + '_right'
    nombres_frases_left = os.listdir(outputdir_img_left)
    nombres_frases_right = os.listdir(outputdir_img_right)

    # For SVG for different phases of the analysis
    """
    for nombre_frase in nombres_frases:
        if 'rewriten_complete' in nombre_frase:
            nombres_frases_rewriten_complete.append(nombre_frase)
        elif 'rewriten' in nombre_frase:
            nombres_frases_rewriten.append(nombre_frase)
        else:
            nombres_frases_original.append(nombre_frase)
    """

    # Colouring left trees
    for nombre_frase_left in nombres_frases_left:

        for key in colors_left:
            color = colors_left[key]

            # Conllu transformation of the GRS output unordered graph
            with open(outputdir_img_left + '/' + nombre_frase_left, "r+") as f:
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

    # Colouring right trees
    for nombre_frase_right in nombres_frases_right:

        for key in colors_right:
            color = colors_right[key]

            # Conllu transformation of the GRS output unordered graph
            with open(outputdir_img_right + '/' + nombre_frase_right, "r+") as f:
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
    
        <script>
            function SyncScroll(page) {
              var div1 = document.getElementById("left");
              var div2 = document.getElementById("right");
              if (page=="left") {
                div2.scrollTop = div1.scrollTop;
              }
              else {
                div1.scrollTop = div2.scrollTop;
              }
            }
        </script>
    
        <style>
    
            .split {
              height: 100%;
              width: 50%;
              position: fixed;
              z-index: 1;
              top: 0;
              overflow-x: auto;
              padding-top: 20px;
            }
    
            /* Control the left side */
            .original {
              left: 0;
            }
    
            /* Control the right side */
            .rewriten {
              right: 0;
            }
    
        </style>
    
    </head>
    
    <body>
    
        <div class="split original" id="left" onscroll="SyncScroll('left')">
    """

    text_sentences = txt_transformer(dir_output + '/' + nombre + '/' + nombre + '_annotated.conllu')

    # Creating lists of names for the different types of SVG files
    outputdir_img_left = dir_svg + '/' + nombre + '_left'
    outputdir_img_right = dir_svg + '/' + nombre + '_right'
    nombres_imgs_left = os.listdir(outputdir_img_left)
    nombres_imgs_right = os.listdir(outputdir_img_left)

    # Commented generation of different SVGs for different states of the analysis
    """
    nombres_frases_original = list()
    nombres_frases_rewriten = list()
    nombres_frases_rewriten_complete = list()
    for nombre_frase in nombres_frases:
        if 'rewriten_complete' in nombre_frase:
            nombres_frases_rewriten_complete.append(nombre_frase)
        elif 'rewriten' in nombre_frase:
            nombres_frases_rewriten.append(nombre_frase)
        else:
            nombres_frases_original.append(nombre_frase)
    """

    n_sentence = 0
    left_img_html = ""
    nombres_imgs_left.sort()

    for nombre_img in nombres_imgs_left:
        left_img_html = left_img_html + '\t\t\t' + '<p>' + text_sentences[n_sentence] + '</p>' + '\n\t\t\t<a href="../svg/' + nombre + '_left/' + nombre_img + '" target="_blank"><img src="../svg/' + nombre + '_left/' + nombre_img + '" border="1" width="100%"></a>' + '\n'
        n_sentence += 1

    n_sentence = 0
    right_img_html = ""
    nombres_imgs_right.sort()

    for nombre_img in nombres_imgs_right:
        right_img_html = right_img_html + '\t\t\t' + '<p>' + text_sentences[n_sentence] + '</p>' + '\n\t\t\t<a href="../svg/' + nombre + '_right/' + nombre_img + '" target="_blank"><img src="../svg/' + nombre + '_right/' + nombre_img + '" border="1" width="100%"></a>' + '\n'
        n_sentence += 1

    html = html + '\n' + left_img_html + """
        </div>

        <div class="split rewriten" id="right" onscroll="SyncScroll('right')">
    """

    html = html + '\n' + right_img_html + """
        </div>
    
    </body>
</html>
    """

    # Creating the HTML file in the template folder
    with open('templates/' + nombre + '.html', "w") as h:
        h.write(html)


# Opening a new tab in browser with the results for selected texts
texts_to_show_after_execution = [
    '3_19991101_ssd',
    '1_20000702_ssd',
    '10_20020102_ssd'
]
for text in texts_to_show_after_execution:
    webbrowser.open('templates/' + text + '.html', new=1, autoraise=True)
