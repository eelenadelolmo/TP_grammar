from conllu import parse
import collections
import re


# Transforms a list of unordered Grew graphs into a list or ordered Grew graphs
def order_graphs(gs):
    grafo_ordenado_list = list()
    for g in gs:
        grafo_ordenado = dict()
        for clave in g:
            if not clave == 'ROOT':
                grafo_ordenado['W' + clave] = g[clave]
            else:
                grafo_ordenado[clave] = g[clave]
        for clave in grafo_ordenado:
            for dep in grafo_ordenado[clave][1]:
                dep[1] = "W" + dep[1]
        grafo_ordenado_list.append(grafo_ordenado)
    return grafo_ordenado_list


# Transforms a list of ordered Grew graphs into a list or unordered Grew graphs
def disorder_graphs(ordered_graphs):
    unordered_graphs = list()
    for g in ordered_graphs:
        g_int = dict()
        for clave in g:
            if not clave == 'ROOT':
                g_int[clave[1:]] = g[clave]
            else:
                g_int[clave] = g[clave]
        for clave in g_int:
            if not clave == 'ROOT':
                for dep in g_int[clave][1]:
                    dep[1] = dep[1][1:]
        unordered_graphs.append(g_int)
    return unordered_graphs


# Transforms a Grew graph into a conllu formatted sentence
def to_conllu(graph):

    conllu_str = ""
    heads = dict()

    for key in graph.keys():
        if not key == 'ROOT':
            heads[int(key)] = list()
            for token in graph:
                if not token == 'ROOT':
                    for dep in graph[token][1]:
                        if int(dep[1]) == int(key):
                            heads[int(key)].append(int(token))
                            heads[int(key)].append(dep[0])

    graph_int = dict()
    for clave in graph:
        if not clave == 'ROOT':
            graph_int[int(clave)] = graph[clave]
        for clave in graph_int:
            for dep in graph_int[clave][1]:
                dep[1] = int(dep[1])

    graph_ordered = collections.OrderedDict(sorted(graph_int.items()))
    for key in graph_ordered.keys():
        if not key == 'ROOT':
            conllu_str += str(key)
            conllu_str += '\t'
            morph = graph_ordered[key][0]
            conllu_str += morph['form']
            conllu_str += '\t'
            conllu_str += morph['lemma']
            conllu_str += '\t'
            conllu_str += morph['upos']
            conllu_str += '\t'
            conllu_str += morph['xpos']
            conllu_str += '\t'
            conllu_str = conllu_str + 'matched=' + morph['matched'] + '|recursive=' + morph['recursive']
            conllu_str += '\t'
            conllu_str += str(heads[key][0]) if len(heads[key]) == 2 else '0'
            conllu_str += '\t'
            conllu_str += str(heads[key][1]) if len(heads[key]) == 2 else 'root'
            conllu_str += '\n'

    return conllu_str


# Annotates the subtree dependency nodes of a node in a conllu formatted file
# The annotation is performed when a node contains the feature recursive with the value yes
def annotator_recursive(conllu_file):
    input = open(conllu_file, "r", encoding="utf-8")
    sentences = parse(input.read())
    resultado = ""


    for sentence in sentences:

        while "recursive=yes" in sentence.serialize():
            hijos = sentence.to_tree().children
            padre = None

            # Getting the recursive:yes token as a subtree
            while len(hijos) > 0 and padre is None:
                for hijo in hijos:
                    if hijo.token['feats']['matched'] == 'yes' and hijo.token['feats']['recursive'] == 'yes':
                        padre = hijo
                        padre.token['feats']['recursive'] = 'no'
                        break
                nietos = []
                for hijo in hijos:
                    nietos.extend(hijo.children)
                hijos = nietos
            if padre is not None:
                hijos = padre.children

            # Annotating all children
            while len(hijos) > 0:
                for hijo in hijos:
                    hijo.token['feats']['matched'] = 'yes'
                nietos = []
                for hijo in hijos:
                    nietos.extend(hijo.children)
                hijos = nietos

        resultado = resultado + re.sub("\|recursive=no", "", sentence.serialize())
    return resultado
