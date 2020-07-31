from utils import order_graphs, disorder_graphs, to_conllu, annotator_recursive
from conllu import parse
import grew

# Install Grew and its requirements, and the Grew package must be loaded for the project. Installation nstructions can be found here: http://grew.fr/install/
# conll must also be installed (via pip for example) and the package must be loaded for the project
# Module working with Python 3.8 interpreter and PyCharm 2020.1 version

## Start Grew tool after importing the library
grew.init()


## Transforming a conllu file into a list of the strings of its sentences

# Input conllu formatted file
conllu_file = 'in/AnCora_Surface_Syntax_Dependencies/conllu/1_20000702_ssd.conllu'

# Temporary file with the text of each sentence
tmp_file = 'out/tmp_sentence.txt'

graphs = list()
input = open(conllu_file, "r", encoding="utf-8")
sentences = parse(input.read())

# Appending every sentence to the graph list object
for sentence in sentences:
    tmp_nf = open(tmp_file, 'w')
    tmp_nf.write(sentence.serialize())
    tmp_nf.close()
    graph = grew.graph(tmp_file)
    graphs.append(graph)


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

## Transforming the Graph object into an ordered one in order to use preceding constrains in rules
ordered_graphs = order_graphs(graphs)
output_graphs = list()

# Appending the unordered output of the GRS application to every ordered Grew graph sentence
for g in ordered_graphs:
    output_graphs.extend(grew.run(rs, g, "S1"))
unordered_graphs = disorder_graphs(output_graphs)

path_to_output_conllu = 'out/output.conllu'
path_to_output_conllu_recursive = 'out/output_recursive.conllu'

# Conllu transformation of the GRS output unordered graph
with open(path_to_output_conllu, "w") as output:
    for e in unordered_graphs:
        output.write(to_conllu(e) + '\n')

# Recursive subtree annotation for recursive=yes featured nodes
with open(path_to_output_conllu_recursive, "w") as output:
    output.write(annotator_recursive(path_to_output_conllu) + '\n')
