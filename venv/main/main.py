from utils import order_graphs, disorder_graphs, to_conllu, annotator_recursive
from conllu import parse
import grew
import os
import shutil
import webbrowser

# Install Grew and its requirements, and the Grew package must be loaded for the project. Installation nstructions can be found here: http://grew.fr/install/
# conll must also be installed (via pip for example) and the package must be loaded for the project
# Module working with Python 3.8 interpreter and PyCharm 2020.1 version


## Start Grew tool after importing the library
grew.init()


## Loading a Grew grs (Graph Rewriting System)
# Documentation can be found here: http://grew.fr/grs/
# More information on rules (embedded in GRS) can be found here: http://grew.fr/rule/
# More information on commands (embedded in rules) can be found here: http://grew.fr/commands/

rs = grew.grs("""
rule preceding_subject {
  pattern {
    X -[root]-> R;
    R -[nsubj]-> S;
    S << R;
  }
  commands {
    S.matched=yes;
    S.recursive=yes;
  }
}

rule probando_preceding {
  pattern {
    N1 [form="Casi"];
    N2 [form="todos"];
    N1 < N2;
    }
  commands {
    N1.form=CASI;
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
    N2.matched=yes;
    N2.recursive=yes
  }
}

strat S1 { Try ( Iter ( Alt (preceding_subject, probando_preceding, subordinate_subject) ) ) }
""")

"""
rule probando_varios_recursive {
  pattern {
    N1 -[pobj]-> N2;
  }
  commands {
    N2.matched=yes;
    N2.recursive=yes;
  }
}
"""


## Transforming a conllu file into a list of the strings of its sentences

# Temporary file with the text of each sentence
tmp_file = 'out/tmp_sentence.txt'

# Input directory
inputdir = 'in/AnCora_Surface_Syntax_Dependencies/conllu'
directory = os.listdir(inputdir)

for f in directory:
    if f.endswith(".conllu"):
        f_noExt = f[:-7]

    input = open(inputdir + '/' + f, "r", encoding="utf-8")
    sentences = parse(input.read())
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
        output_graphs.extend(grew.run(rs, g, "S1"))
    unordered_graphs = disorder_graphs(output_graphs)

    # Deleting previous output directories and creating them again
    path_to_output_conllu = 'out/' + f_noExt + '/'
    shutil.rmtree(path_to_output_conllu, ignore_errors=True)
    os.makedirs(path_to_output_conllu)

    # Conllu transformation of the GRS output unordered graph
    with open(path_to_output_conllu + f_noExt + '_annotated.conllu', "w") as output:
        for e in unordered_graphs:
            output.write(to_conllu(e) + '\n')

    # Recursive subtree annotation for recursive=yes featured nodes
    with open(path_to_output_conllu + f_noExt + '_annotated_recursive.conllu', "w") as output:
        output.write(annotator_recursive(path_to_output_conllu + f_noExt + '_annotated.conllu') + '\n')

os.remove('/home/elena/PycharmProjects/TP_grammar/venv/main/out/tmp_sentence.txt')


## Creating one folder for every text containing the SVG files os their sentences trees:
# - the original,
# - the rewriten one and
# - the rewriten one containing aditional features)

# Deleting previous output SVG directories and creating them again (subfolder creation inside loop)
inputdir_svg = '/home/elena/PycharmProjects/TP_grammar/venv/main/svg'
directory = os.listdir(inputdir_svg)
shutil.rmtree(inputdir_svg, ignore_errors=True, onerror=None)
os.makedirs(inputdir_svg)

# For relative commands execution
os.chdir("/home/elena/PycharmProjects/TP_grammar/venv/main")

outputdir = '/home/elena/PycharmProjects/TP_grammar/venv/main/out'
nombres_textos = os.listdir(outputdir)

for nombre in nombres_textos:

    os.makedirs(inputdir_svg + '/' + nombre)

    comando_gen_original = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '.svg -c in/AnCora_Surface_Syntax_Dependencies/conllu/' + nombre + '.conllu --ignore-double-indices'
    comando_gen_rewriten = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '_rewriten.svg -c out/' + nombre + '/' + nombre + '_annotated_recursive.conllu --ignore-double-indices'
    comando_gen_rewriten_complete = 'python3 conll_viewer/dependency2tree.py -o svg/' + nombre + '/' + nombre + '_rewriten_complete.svg -c out/' + nombre + '/' + nombre + '_annotated_recursive.conllu --ignore-double-indices --feats'

    os.system(comando_gen_original)
    os.system(comando_gen_rewriten)
    os.system(comando_gen_rewriten_complete)


## Generating one HTML file with the original and rewriten trees of every text

shutil.rmtree('/home/elena/PycharmProjects/TP_grammar/venv/main/templates', ignore_errors=True)
os.makedirs('/home/elena/PycharmProjects/TP_grammar/venv/main/templates')

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

    outputdir_img = '/home/elena/PycharmProjects/TP_grammar/venv/main/svg/' + nombre
    nombres_frases = os.listdir(outputdir_img)
    nombres_frases_original = list()
    nombres_frases_rewriten = list()
    nombres_frases_rewriten_complete = list()

    # Creating lists of names for the different types of SVG files
    for nombre_frase in nombres_frases:
        if 'rewriten_complete' in nombre_frase:
            nombres_frases_rewriten_complete.append(nombre_frase)
        elif 'rewriten' in nombre_frase:
            nombres_frases_rewriten.append(nombre_frase)
        else:
            nombres_frases_original.append(nombre_frase)

    original_img_html = ""
    nombres_frases_original.sort()
    for nombre_frase_original in nombres_frases_original:
        original_img_html = original_img_html + '\t\t\t' + '<a href="../svg/' + nombre + '/' + nombre_frase_original + '" target="_blank"><img src="../svg/' + nombre + '/' + nombre_frase_original + '" border="1" width="100%"></a>' + '\n'

    rewriten_img_html = ""
    nombres_frases_rewriten.sort()
    for nombre_frase_rewriten in nombres_frases_rewriten:
        rewriten_img_html = rewriten_img_html + '\t\t\t' + '<a href="../svg/' + nombre + '/' + nombre_frase_rewriten[:-8] + '_complete' + nombre_frase_rewriten[-8:] + '" target="_blank"><img src="../svg/' + nombre + '/' + nombre_frase_rewriten + '" border="1" width="100%"></a>' + '\n'

    html = html + '\n' + original_img_html + """
        </div>

        <div class="split rewriten" id="right" onscroll="SyncScroll('right')">
    """

    html = html + '\n' + rewriten_img_html + """
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
    patch_html = "templates/example.html"
    webbrowser.open('templates/' + text + '.html', new=1, autoraise=True)
