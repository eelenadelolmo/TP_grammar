from utils import order_graphs, disorder_graphs, to_conllu, annotator_recursive
from conllu import parse
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
dir_original = 'in/AnCora_Surface_Syntax_Dependencies/conllu'

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


## Creating different simpler subgrammars (in order to avoid GrewError: 'More than 10000 rewriting steps: ckeck for loops or increase max_rules value')
grs_list = list()

grs_preceding_subject = """
rule preceding_subject {
  pattern {
    X -[root]-> R;
    R -[nsubj]-> S;
    S << R;
  }
  commands {
    S.theme=yes;
    S.recursive=yes;
  }
}

rule subordinate_subject {
  pattern {
    N1 -[nsubj]-> N2;
    }
  without {
    N0 -[root]-> N1;
  }
  commands {
    N2.theme=yes;
    N2.recursive=yes;
  }
}

strat S1 { Try ( Iter ( Alt (preceding_subject, subordinate_subject) ) ) }
"""

grs_main_reported_clause = """
rule subordinate_dobj_clause {
  pattern {
    N0 -[dobj]-> N1;
    N1 -[cobj]-> N2;
  }
  commands {
    N1.main=yes;
    N1.recursive=yes;
  }
}

strat S1 { Try ( Iter ( Alt (subordinate_dobj_clause) ) ) }
"""

grs_list.append(grs_preceding_subject)
grs_list.append(grs_main_reported_clause)

n_gram = 0
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
                output_graphs.extend(grew.run(gram, g, "S1"))
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
                output_graphs.extend(grew.run(gram, g, "S1"))
            unordered_graphs = disorder_graphs(output_graphs)

            ruta = dir_output + '/' + f_noExt + '/'
            with open(ruta + f_noExt + '_annotated.conllu', "w") as output:
                for e in unordered_graphs:
                    output.write(to_conllu(e) + '\n')

            # Recursive subtree annotation for recursive=yes featured nodes
            with open(ruta + f_noExt + '_annotated_recursive.conllu', "w") as output:
                output.write(annotator_recursive(dir_output + '/' + f_noExt + '/' + f_noExt + '_annotated.conllu') + '\n')

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

    comando_gen_original = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '.svg -c in/AnCora_Surface_Syntax_Dependencies/conllu/' + nombre + '.conllu --ignore-double-indices'
    comando_gen_rewriten = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '_rewriten.svg -c out/' + nombre + '/' + nombre + '_annotated_recursive.conllu --ignore-double-indices'
    comando_gen_rewriten_complete = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '_rewriten_complete.svg -c out/' + nombre + '/' + nombre + '_annotated_recursive.conllu --ignore-double-indices --feats'

    # os.system(comando_gen_original)
    # os.system(comando_gen_rewriten)
    os.system(comando_gen_rewriten_complete)


## Generating one HTML file with the original and rewriten trees of every text

for nombre in nombres_textos:
    html = """<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Drawing the trees for the sentences in the text</title>
    
        <script>
            function SyncScroll(phoneFaceId) {
              var div1 = document.getElementById("left");
              var div2 = document.getElementById("right");
              if (phoneFaceId=="left") {
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

    # Creating lists of names for the different types of SVG files
    outputdir_img = dir_svg + '/' + nombre
    nombres_frases = os.listdir(outputdir_img)
    nombres_frases_rewriten_complete = list()
    for nombre_frase in nombres_frases:
        nombres_frases_rewriten_complete.append(nombre_frase)

    # Commented generation of different SVGs for differentes states of the analysis
    """
    nombres_frases_original = list()
    nombres_frases_rewriten = list()
    for nombre_frase in nombres_frases:
        if 'rewriten_complete' in nombre_frase:
            nombres_frases_rewriten_complete.append(nombre_frase)
        elif 'rewriten' in nombre_frase:
            nombres_frases_rewriten.append(nombre_frase)
        else:
            nombres_frases_original.append(nombre_frase)
    """

    left_img_html = ""
    nombres_frases_rewriten_complete.sort()
    for nombre_frase_rewriten_complete in nombres_frases_rewriten_complete:
        left_img_html = left_img_html + '\t\t\t' + '<a href="../svg/' + nombre + '/' + nombre_frase_rewriten_complete + '" target="_blank"><img src="../svg/' + nombre + '/' + nombre_frase_rewriten_complete + '" border="1" width="100%"></a>' + '\n'

    right_img_html = ""
    nombres_frases_rewriten_complete.sort()
    for nombre_frase_rewriten_complete in nombres_frases_rewriten_complete:
        right_img_html = right_img_html + '\t\t\t' + '<a href="../svg/' + nombre + '/' + nombre_frase_rewriten_complete + '" target="_blank"><img src="../svg/' + nombre + '/' + nombre_frase_rewriten_complete + '" border="1" width="100%"></a>' + '\n'

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


## Colouring in background green nodes corresponding to main clauses

# Creating the dictionary of annotation types and the corresponding color for the ellipses containing that feature
# colors_right = {'main': '#98D2A5', 'theme': '#BEDA48'}            # Testing more than one
# colors_left = {'main': '#98D2A5'}                                 # Definitive
# colors_right = {'theme': '#BEDA48', 'rheme': '#DA8D48'}           # Definitive

colors_left = {'main': '#98D2A5'}
colors_right = {'theme': '#BEDA48'}

# Selecting the SVG files to color
for nombre in nombres_textos:
    outputdir_img = '/home/elena/PycharmProjects/TP_grammar/venv/main/svg/' + nombre
    nombres_frases = os.listdir(outputdir_img)
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

    for nombre_frase_rewriten_complete in nombres_frases_rewriten_complete:

        for key in colors_right:
            color = colors_right[key]

            # Conllu transformation of the GRS output unordered graph
            with open(outputdir_img + '/' + nombre_frase_rewriten_complete, "r+") as f:
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


# Opening a new tab in browser with the results for selected texts
texts_to_show_after_execution = [
    '3_19991101_ssd',
    '1_20000702_ssd',
    '10_20020102_ssd'
]
for text in texts_to_show_after_execution:
    webbrowser.open('templates/' + text + '.html', new=1, autoraise=True)
