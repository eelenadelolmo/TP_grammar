from utils import order_graphs, disorder_graphs, to_conllu, annotator_recursive
from flask import Flask, flash, request, redirect, send_file, render_template, url_for
from werkzeug.utils import secure_filename
from conllu import parse
import pyconll as pc
import webbrowser
import secrets
import natsort
import shutil
import grew
import os
import io
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
dir_original = 'in'

# Output directory
dir_output = 'out'
shutil.rmtree(dir_output, ignore_errors=True)
os.makedirs(dir_output)

# Temporary file with the text of each sentence
tmp_file = dir_output + '/tmp_sentence.txt'

# SVG directory for showing after execution
# dir_svg = 'svg'
# shutil.rmtree(dir_svg, ignore_errors=True, onerror=None)
# os.makedirs(dir_svg)

# HTML directory for showing after execution
# dir_html = 'html_trees'
# shutil.rmtree(dir_html, ignore_errors=True)
# os.makedirs(dir_html)

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
        s_txt = re.sub(r" ([.,:?!])", r"\1", s_txt)
        s_txt = re.sub(r" ([)])", r"\1", s_txt)
        s_txt = re.sub(r"([(]) ", r"\1", s_txt)
        s_txt = re.sub(r"([¿]) ", r"\1", s_txt)
        s_txt = re.sub(r"&quot; (.+?) &quot;", r'"\1"', s_txt)
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

def make_archive(source, destination):
        base = os.path.basename(destination)
        name = base.split('.')[0]
        format = base.split('.')[1]
        archive_from = os.path.dirname(source)
        archive_to = os.path.basename(source.strip(os.sep))
        shutil.make_archive(name, format, archive_from, archive_to)
        shutil.move('%s.%s'%(name,format), destination)

UPLOAD_FOLDER = dir_original
DOWNLOAD_FOLDER = dir_output
ALLOWED_EXTENSIONS_txt = {'txt'}
ALLOWED_EXTENSIONS_conll = {'conll'}
ALLOWED_EXTENSIONS_conllu = {'conllu'}

def allowed_file(filename, extension):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extension

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def add_header(response):
  response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
  if ('Cache-Control' not in response.headers):
    response.headers['Cache-Control'] = 'public, max-age=600'
  return response

@app.route('/upload-grew-ann')
def upload_form():
    shutil.rmtree(UPLOAD_FOLDER + '/', ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER + '/')
    return render_template('upload_grew_ann_en.html')

@app.route('/upload-grew-ann', methods=['POST'])
def upload_file():
    if request.method == 'POST':

        # shutil.rmtree(UPLOAD_FOLDER + '/', ignore_errors=True)
        # os.makedirs(UPLOAD_FOLDER + '/')
        shutil.rmtree(DOWNLOAD_FOLDER + '/', ignore_errors=True)
        os.makedirs(DOWNLOAD_FOLDER + '/')

        # check if the post request has the file part
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        # if user does not select file, browser also
        # submit an empty part without filename
        for file in files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_conll):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file.stream.seek(0)

    return render_template('upload_grew_ann_en.html')


@app.route('/annotate', methods=['POST'])
def annotate():

    shutil.rmtree(DOWNLOAD_FOLDER + '/', ignore_errors=True)
    os.makedirs(DOWNLOAD_FOLDER + '/')

    files_conllu = list()

    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.split('.')[-1] == 'conllu':
            files_conllu.append(filename)
        elif filename.split('.')[-1] == 'grew':
            # Creating different simpler subgrammars (in order to avoid GrewError: 'More than 10000 rewriting steps: ckeck for loops or increase max_rules value')
            with io.open(UPLOAD_FOLDER + "/" + filename, 'r') as f:
                raw = f.read()
                grs_list = raw.split('####')

    # Ordering matters:
    # the features generated by the previous rule strategies are available for the subsequent ones no matter the strategies defined

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


        if n_gram == 1:

            for file in files_conllu:
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
                        salida = grew.run(gram, g, "S1")
                        output_graphs.extend(salida)
                        if len(salida) > 1:
                            print(grs[:grs.find('{')], '-  produce', len(salida), 'grafos  en el archivo', file,
                                  'en la frase', g['W1'][0]['form'], g['W2'][0]['form'], g['W3'][0]['form'],
                                  g['W4'][0]['form'], '...')
                        n_processed += 1
                    except grew.utils.GrewError:
                        output_graphs.extend([g])
                        n_exceptions += 1
                        print('\nFALLO:', grs[:grs.find('{')], '-  falla  en el archivo', file, 'en la frase',
                              g['W1'][0]['form'], g['W2'][0]['form'], g['W3'][0]['form'], g['W4'][0]['form'], '...')
                unordered_graphs = disorder_graphs(output_graphs)

                ruta = dir_output + '/' + f_noExt + '/'
                with open(ruta + f_noExt + '_annotated.conllu', "w") as output:
                    for e in unordered_graphs:
                        output.write(to_conllu(e) + '\n')

                # Recursive subtree annotation for recursive=yes featured nodes
                with open(ruta + f_noExt + '_annotated_recursive.conllu', "w") as output:
                    output.write(
                        annotator_recursive(dir_output + '/' + f_noExt + '/' + f_noExt + '_annotated.conllu') + '\n')


        else:

            dir_output_files = os.listdir(dir_output)
            for file in dir_output_files:
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
                        salida = grew.run(gram, g, "S1")
                        output_graphs.extend(salida)
                        if len(salida) > 1:
                            print(grs[:grs.find('{')], '-  produce', len(salida), 'grafos en el archivo', file,
                                  'en la frase', g['W1'][0]['form'], g['W2'][0]['form'], g['W3'][0]['form'],
                                  g['W4'][0]['form'], '...')
                        n_processed += 1
                    except grew.utils.GrewError:
                        output_graphs.extend([g])
                        n_exceptions += 1
                        print('\nFALLO:', grs[:grs.find('{')], '-  falla en el archivo', file, 'en la frase',
                              g['W1'][0]['form'], g['W2'][0]['form'], g['W3'][0]['form'], g['W4'][0]['form'], '...')

                unordered_graphs = disorder_graphs(output_graphs)

                ruta = dir_output + '/' + f_noExt + '/'
                with open(ruta + f_noExt + '_annotated.conllu', "w") as output:
                    for e in unordered_graphs:
                        output.write(to_conllu(e) + '\n')

                # Recursive subtree annotation for recursive=yes featured nodes
                with open(ruta + f_noExt + '_annotated_recursive.conllu', "w") as output:
                    output.write(annotator_recursive(dir_output + '/' + f_noExt + '/' + f_noExt + '_annotated.conllu') + '\n')


    print('--------------------------------------------------------------------------------')
    print('Numero de estrategias aplicadas correctamente: ' + str(n_processed))
    print('Numero de estrategias erróneas: ' + str(n_exceptions))
    os.remove(tmp_file)


    ## Creating one folder for every text containing the SVG files os their sentences trees:
    # - the original,
    # - the rewriten one and
    # - the rewriten one containing additional features)

    # For relative commands execution
    # os.chdir("venv/main")

    nombres_textos = os.listdir(DOWNLOAD_FOLDER)
    for_zip = 'out_zip/out'
    shutil.rmtree(for_zip, ignore_errors=True)
    os.makedirs(for_zip)
    for_zip_grew_svg = 'out_zip/out/svg'
    os.makedirs(for_zip_grew_svg)

    for nombre in nombres_textos:
        os.makedirs(for_zip_grew_svg + '/' + nombre)
        ruta_input = dir_output + '/' + nombre + '/' + nombre + '_annotated_recursive.conllu'

        # Deleting unnecessary features
        with open(ruta_input, 'r+') as f:
            raw = f.read()
            raw = re.sub('\|main=', '|m=', raw)
            raw = re.sub('\|theme=', '|t=', raw)
            raw = re.sub('\|rheme=', '|r=', raw)
            raw = re.sub('\|coord=', '|c=', raw)
            raw = re.sub('recursive=(yes|no)\|', '', raw)
            f.close()
        with open(ruta_input, 'w') as f:
            f.write(raw)

        comando_gen_rewriten_complete = 'python3 conll_viewer/dependency2tree.py -o ' + for_zip_grew_svg + '/' + nombre + '/' + nombre + '_rewriten_complete.svg -c ' + ruta_input + ' --ignore-double-indices --feats'
        os.system(comando_gen_rewriten_complete)

        # comando_gen_original = 'python3 conll_viewer/dependency2tree.py -o ' + dir_svg + '/' + nombre + '/' + nombre + '.svg -c in/AnCora_Surface_Syntax_Dependencies/conllu/' + nombre + '.conllu --ignore-double-indices'
        # comando_gen_rewriten = 'python3 conll_viewer/dependency2tree.py -o ' + dir_svg + '/' + nombre + '/' + nombre + '_rewriten.svg -c ' + dir_output + '/' + nombre + '/' + nombre + '_annotated_recursive.conllu --ignore-double-indices'
        # os.system(comando_gen_original)
        # os.system(comando_gen_rewriten)

    # Creating folders for both left and right trees in order to visualy compare, mainly:
    # - Overlapping annotations
    # - Subordinate annotations (that depends on another previous annotation)

    for d in os.listdir(for_zip_grew_svg):
        os.makedirs(for_zip_grew_svg + '/' + d + '_right')
        copytree(for_zip_grew_svg + '/' + d, for_zip_grew_svg + '/' + d + '_right')
        os.rename(for_zip_grew_svg + '/' + d, for_zip_grew_svg + '/' + d + '_left')

    ## Colouring specific nodes

    # Creating the dictionary of annotation types and the corresponding color for the ellipses containing that feature
    # colors_right = {'main': '#98D2A5', 'theme': '#BEDA48'}            # Testing more than one
    # colors_left = {'main': '#98D2A5'}                                 # Definitive
    # colors_right = {'theme': '#BEDA48', 'rheme': '#DA8D48'}           # Definitive

    colors_left = {'m': '#98D2A5'}
    colors_right = {'t': '#BEDA48', 'r': '#DA79E8'}

    # Selecting the SVG files to color
    for nombre in nombres_textos:
        outputdir_img_left = for_zip_grew_svg + '/' + nombre + '_left'
        outputdir_img_right = for_zip_grew_svg + '/' + nombre + '_right'
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
    ## Generating one txt file for every sentence of every text

    for_zip_grew_html = 'out_zip/out/html'
    os.makedirs(for_zip_grew_html)

    for_zip_grew_txt = 'out_zip/out/txt'
    os.makedirs(for_zip_grew_txt)


    for_zip_grew_conllu = 'out_zip/out/conllu'
    os.makedirs(for_zip_grew_conllu)

    nombres_textos = os.listdir(DOWNLOAD_FOLDER)
    for nombre in nombres_textos:
        for_copy = dir_output + '/' + nombre + '/' + nombre + '_annotated_recursive.conllu'
        shutil.copyfile(for_copy, for_zip_grew_conllu + '/' + nombre + '.conllu')



    nombres_archivos = os.listdir(DOWNLOAD_FOLDER)
    for nombre in nombres_archivos:
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
        outputdir_img_left = for_zip_grew_svg + '/' + nombre + '_left'
        outputdir_img_right = for_zip_grew_svg + '/' + nombre + '_right'
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
        nombres_imgs_left = natsort.natsorted(nombres_imgs_left)

        for nombre_img in nombres_imgs_left:
            left_img_html = left_img_html + '\t\t\t' + '<p>' + text_sentences[
                n_sentence] + '</p>' + '\n\t\t\t<a href="../svg/' + nombre + '_left/' + nombre_img + '" target="_blank"><img src="../svg/' + nombre + '_left/' + nombre_img + '" border="1" width="100%"></a>' + '\n'
            n_sentence += 1

        n_sentence = 0
        right_img_html = ""
        nombres_imgs_right = natsort.natsorted(nombres_imgs_right)

        for nombre_img in nombres_imgs_right:
            right_img_html = right_img_html + '\t\t\t' + '<p>' + text_sentences[
                n_sentence] + '</p>' + '\n\t\t\t<a href="../svg/' + nombre + '_right/' + nombre_img + '" target="_blank"><img src="../svg/' + nombre + '_right/' + nombre_img + '" border="1" width="100%"></a>' + '\n'
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
        with open(for_zip_grew_html + '/' + nombre + '.html', "w") as h:
            h.write(html)

        # Creating the txt file in the txt folder
        n_sentences = 0
        for text_sentence in text_sentences:
            if len(text_sentence) > 1:
                n_sentences += 1
                with io.open(for_zip_grew_txt + '/' + nombre + '_' + str(n_sentences) + '.txt', 'w', encoding='utf8') as f_new:
                    f_new.write(text_sentence)
                    f_new.close()




    make_archive(for_zip, DOWNLOAD_FOLDER + '/' + 'grew_annotated.zip')
    return redirect(url_for('download_file_grew_ann', filename='grew_annotated.zip'))


@app.route("/downloadfile-grew-ann/<filename>", methods = ['GET'])
def download_file_grew_ann(filename):
    return render_template('download_grew_ann_en.html', value=filename)

@app.route('/return-files-grew-ann/<filename>', methods = ['GET'])
def return_files_tut_2(filename):
    file_path = DOWNLOAD_FOLDER + '/grew_annotated.zip'
    return send_file(file_path, as_attachment=True, cache_timeout=0)


if __name__ == "__main__":
    secret = secrets.token_urlsafe(32)
    app.secret_key = secret
    app.run(host='0.0.0.0', port="5000")




# Opening a new tab in browser with the results for selected texts

"""
texts_to_show_after_execution = [
    '3_19991101_ssd',
    '1_20000702_ssd',
    '10_20020102_ssd'
]
for text in texts_to_show_after_execution:
    webbrowser.open(dir_html + '/' + text + '.html', new=1, autoraise=True)
"""