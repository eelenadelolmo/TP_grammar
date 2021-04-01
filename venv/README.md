## Grew-based intraorational thematic annotation


### Installation

Clone the repo and execute the installation command:
`pip install -r requirements.txt`


### Usage

- For Spanish annotation: run main_webapp.py and upload your files to http://0.0.0.0:5000/upload-grew-ann
- For English annotation: run main_webapp_en.py and upload your files to http://0.0.0.0:5000/upload-grew-ann 

Your text files to annotated must be in CoNLL-U format (https://universaldependencies.org/format.html)

Your grammar file must contain a list of Grew strategies (https://grew.fr/doc/grs/). 

Each strategy is applied sequentially and their output is the input for the subsequent strategies. 
The separator between strategies is `####`.

Recursive subtree annotation is available by means of annotating the head node of the subtree to annotate with a `recursive=yes` feature in a strategy. The new features of the node are propagated recursively to its child nodes.
 
____
 
This project is a part of a PhD thesis carried out at the Department of Linguistics of the Complutense University of Madrid (https://www.ucm.es/linguistica/grado-linguistica) and is supported by the ILSA (Language-Driven Software and Applications) research group (http://ilsa.fdi.ucm.es/).