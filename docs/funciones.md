# Funciones del módulo de anotación temática

Documentación de las funciones de `venv/main/utils.py`, que usan `main.py` y `main_webapp.py` (apartado 6.8.1 de la tesis).

## Directorios de trabajo

El módulo funciona con el intérprete de Python 3.8 y trabaja con cuatro directorios:

- El directorio con los archivos de entrada en formato CoNLL-U (`dir_original`).
- El directorio con los archivos de salida en formato CoNLL-U (`dir_output`).
- El directorio con los archivos de salida en formato SVG (`dir_svg`).
- El directorio con los archivos de salida en formato HTML (`dir_html`).

Los directorios de salida se vacían antes de cada ejecución del programa.

## Funciones

La función `order_graphs` toma como argumento una lista de grafos de Grew y devuelve una lista de grafos cuyos nodos están ordenados por precedencia lineal en la oración. En el módulo, todos los grafos de un texto se transforman en grafos ordenados previamente a la ejecución de las estrategias de anotación. Posteriormente, la función `disorder_graphs`, al contrario, vuelve a transformar los grafos ordenados de vuelta al formato de grafos de Grew.

Se ha diseñado otra función, `to_conllu`, para transformar de vuelta la salida en forma de grafo de la anotación de las estrategias de Grew al estándar CoNLL-U (Buchholz & Marsi, 2006), de tal manera que la salida de cada ejecución pueda utilizarse como entrada para la siguiente.

Como Grew no permite anotar subárboles completos, la función `annotator_recursive_main`, que toma como argumento la ruta hasta un fichero en formato CoNLL-U, se ha diseñado de tal manera que busca todos los nodos que contienen el rasgo `recursive` con el valor “yes” y propaga a todos los nodos del subárbol el resto de sus rasgos. Para que la estrategia implementada funcione, el experto de dominio lingüista encargado de codificar las reglas debe seguir la convención de actualizar el rasgo `recursive` con el valor “yes” en los casos en que los rasgos de un nodo deban propagarse a sus hijos recursivamente.

La función `annotator_recursive_in_main` hace la misma propagación, pero solo a los nodos que pertenecen a la cláusula analizada (rasgo `main` con el valor “yes”). Se emplea con las estrategias que operan dentro de dicha cláusula.
