# Estrategias de anotación y reglas en formato Grew

Estrategias y reglas Grew del módulo de anotación temática del prototipo (apartado 6.8.1 de la tesis) y del tratamiento de la coordinación (apartado 6.8.1.1). El código ejecutable está en `venv/main/grams.grew` y `venv/main/main.py`; la sintaxis de Grew se describe en [`sintaxis_grew.md`](sintaxis_grew.md) y las funciones auxiliares en [`funciones.md`](funciones.md).

- [1. Estrategias para la anotación temática](#1-estrategias-para-la-anotación-temática)
- [2. Estrategias para el tratamiento de la coordinación](#2-estrategias-para-el-tratamiento-de-la-coordinación)

## 1. Estrategias para la anotación temática

Las estrategias son:

### `grs_main`

La estrategia *grs_main* contiene las reglas *subordinate_dobj_clause* y *main_root* con la estrategia de ejecución condicional de la iteración de la primera, siempre que esta se aplique al menos una vez, y la ejecución simple de la segunda, en el caso de que la primera no se aplique. Ambas reglas se enfocan en la delimitación de la cláusula considerada más relevante en términos informativos. En concreto, la regla *subordinate_dobj_clause* se encarga, (i), de la localización de patrones en los que existe un subárbol cuyo núcleo depende como objeto clausal (*csubj*) de otro nodo que depende como objeto directo (*dobj*) de un tercer nodo del que depende otro nodo con una dependencia de tipo sujeto nominal (*nsubj*) y, (ii), de la anotación del nodo sujeto como constituyente que induce modalidad enunciativa (con el rasgo *rep=yes*) y la anotación recursiva del subárbol con la dependencia de objeto clausal como oración principal. De esta manera, en una oración como *El presidente mantuvo que en la reunión se resolverían todos los asuntos*, en la que existieran las dependencias *nsubj(mantuvo, presidente)*, *dobj(mantuvo, que)* y *cobj(que, resolverían)* y en la que el subárbol a partir del nodo *presidente* agrupara las palabras *el presidente* y el subárbol a partir del nodo *resolverían* agrupara las palabras *se resolverían todos los asuntos*, anotaría como inductor de modalidad enunciativa el subárbol *el presidente* y como oración principal el subárbol *se resolverían todos los asuntos*.

```
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
```

### `grs_solving_weirdAnn`

La estrategia *grs_solving_weirdAnn* contiene una única regla que se ejecuta de manera iterativa generando únicamente un grafo de salida (estrategia de anotación *Onf* o *on-normal-form*). Su finalidad es, (i), localizar estructuras equivalentes en cuanto a categorización lingüística a las descritas en la estrategia interior pero que han sido anotadas, inconsistentemente y con una frecuencia mucho menor, con dos dependencias anidadas de tipo objeto clausal para la conjunción y el verbo principal de la cláusula subordinada y, (ii), modificar el árbol de dependencias de tal manera que la dependencia de la conjunción que introduce la cláusula en cuestión sea de tipo objeto directo (*dobj*) en lugar de tipo objeto clausal (*cobj*), de tal manera que todas las estructuras de este tipo estén anotadas de la misma manera en el corpus. A pesar de que esta regla se presenta inmediatamente a continuación de la que se encarga de añadir información a este tipo de estructuras con un propósito didáctico, su ejecución en el módulo debe, necesariamente, tener lugar con anterioridad a la misma, para así garantizar una cobertura óptima para la misma.

```
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
```

### `grs_nsubj_ellision_rep`

La estrategia *grs_nsubj_ellision_rep* contiene únicamente la regla que se ejecuta de manera iterativa generando únicamente un grafo de salida (estrategia de anotación *Onf*). Se encarga de, (i), localizar patrones que cumplan todas las restricciones declaradas para la regla *subordinate_dobj_clause* descritas anteriormente en los que, además, el verbo principal de la subordinada clausal localizada no presente ningún dependiente de tipo sujeto y, (ii), reescribir el árbol de dependencias de la oración de tal manera que el sujeto del verbo de la oración de la que la subordinada clausal depende directamente pase a depender, con el mismo tipo de dependencia que mantenía originalmente, del verbo principal de dicha subordinada y, además, se le añada a todo el subárbol que encabeza el rasgo que codifica su pertenencia a la oración considerada principal en términos informativos. De esta manera, en una oración como *El responsable prometió que presentaría las conclusiones del trimestre en la próxima reunión*, se anotaría como oración principal *El responsable presentaría las conclusiones del trimestre en la próxima reunión* y se consideraría que, dentro de dicho subárbol, el sintagma *el responsable* depende de *presentaría* como sujeto. Esta regla no está exenta de la sobregeneración de oraciones en las que la recuperación del sujeto es incorrecta. Se prevé la complementación de la misma con reglas que aseguren, al menos, la concordancia, aunque previamente se planifica el estudio cuantitativo de su alcance, ya que la existencia de concordancia no siempre garantiza que sea correcta la inferencia de la correferencia del sujeto elidido (obsérvese por ejemplo el caso de la oración *El presidente en funciones deseó que [la moción de censura] fuera solamente una maniobra destinada a ganar tiempo*), así como tampoco la ausencia de concordancia implica que la correspondencia de los sujetos semánticos de ambas cláusulas no sea correcta (obsérvese por ejemplo el caso de la oración *Los miembros de la junta directiva desmintieron que [la junta directiva] se hubiera reunido en secreto durante los últimos cuatro meses*).

```
grs_nsubj_ellision_rep = """
rule nsubj_ellision_rep {
  pattern {
    X -[root]-> N0;
    N0 -[nsubj]-> S;
    N0 -[dobj]-> N1;
    N1 -[cobj]-> N2;
    N2.upos = re"v.+";
  }
  without {
    N2 -[nsubj]-> S2;
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
```

### `grs_preceding_subjects`

La estrategia *grs_preceding_subjects* consta de una única regla que se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado, es decir, reescribe el grafo tantas veces como le es posible. La finalidad de la regla es, (i), localizar los subárboles con una dependencia de tipo sujeto nominal que se hallen contenidos en un subárbol anotado como oración principal en términos informativos siempre que precedan su núcleo y, (ii), anotar dicho subárbol como Tema de la oración (es decir, incluir el rasgo *theme=yes*).

```
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
```

### `grs_preceding_subject_first`

La estrategia *grs_preceding_subject_first* consta de una única regla que se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado, es decir, reescribe el grafo tantas veces como le es posible. La finalidad de las reglas es, (i), localizar dos subárboles anotados como Tema (gracias a la exigencia de que su núcleo no esté anotado como Tema se consigue delimitar todos los nodos que constituyen dicho Tema) en una oración y deshacer la anotación del que se sitúe más a la derecha en el orden lineal de la misma. Como la ejecución de esta estrategia se establece de manera iterativa, como resultado de su aplicación solamente quedará como máximo un Tema anotado por oración.

```
grs_preceding_subject_first = """
rule preceding_subject_first {
  pattern {
    R1 [ theme="no" ];
    T1 [ theme="yes" ];
    R1 -[nsubj]-> T1;
    R2 [ theme="no" ];
    T2 [ theme="yes" ];
    R2 -[nsubj]-> T2;
    T1 << T2;
  }
  commands {
    T2.theme=no;
    T2.recursive=yes;
  }
}
strat S1 { Try ( Iter ( preceding_subject_first ) ) }
"""
```

### `grs_main_satellites_out`

La estrategia *grs_main_satellites_out* contiene un total de ocho reglas cuya disyunción se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado (es decir, mediante la estrategia anidada de las órdenes *Try*, *Iter* y *Alt*). A continuación, se explica en detalle cada una de estas reglas:

  - La regla *ignore_satellites_root_advmod* tiene como objetivo, (i), localizar los subárboles dependientes del núcleo de la oración con una dependencia del tipo adjunto adverbial (*advmod*) cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho subárbol adjunto adverbial como parte de la cláusula más relevante informativamente.

  - La regla *ignore_satellites_root_advcl* tiene como objetivo, (i), localizar los subárboles dependientes del núcleo de la oración con una dependencia del tipo cláusula adjunta adverbial (*advcl*) cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho subárbol adjunto adverbial como parte de la cláusula más relevante informativamente.

  - La regla *ignore_satellites_root_prepv* tiene como objetivo, (i), localizar los subárboles dependientes del núcleo de la oración con una dependencia del tipo complemento verbal preposicional (*prepv*) cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho subárbol complemento preposicional como parte de la cláusula más relevante informativamente.

  - La regla *ignore_satellites_root_prep* tiene como objetivo funciona de manera análoga a la regla anterior, solo que la dependencia del patrón es de tipo complemento preposicional genérico (*prep*).

  - La regla *ignore_satellites_root_cc* tiene como objetivo, (i), localizar los subárboles dependientes del núcleo de la oración con una dependencia del tipo conjunción coordinante (*cc*) cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho subárbol de tipo conjunción coordinante como parte de la cláusula más relevante informativamente.

  - La regla *ignore_satellites_root_rcmod* tiene como objetivo, (i), localizar los subárboles dependientes del núcleo de la oración con una dependencia del tipo cláusula modificadora de relativo (*rcmod*) cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho subárbol de tipo modificador clausal de relativo como parte de la cláusula más relevante informativamente.

  - La regla *ignore_satellites_root_punct* tiene como objetivo, (i), localizar los nodos dependientes del núcleo de la oración con una dependencia del tipo puntuación (*punct*) cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho nodo de tipo puntuación como parte de la cláusula más relevante informativamente.

  - Por último, la regla *ignore_satellites_root_coord_fixed* tiene como objetivo, (i), localizar los nodos dependientes del núcleo de la oración con una dependencia de tipo *coord_fixed* cuando están incluidos en el subárbol considerado más relevante en términos informativos y, (ii), deshacer la anotación de dicho nodo de tipo puntuación como parte de la cláusula más relevante informativamente. La categoría lingüística representada por esta etiqueta, que no se corresponde con el conjunto original de etiquetas del corpus, se revisará en el apartado siguiente, ya que es parte del módulo de tratamiento de la coordinación.

```
grs_main_satellites_out = """
rule ignore_satellites_root_advmod {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[advmod]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_advcl {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[advcl]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_prepv {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[prepv]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_prep {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[prep]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_cc {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[cc]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_rcmod {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[rcmod]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_punct {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[punct]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
rule ignore_satellites_root_coord_fixed {
  pattern {
    X -[root]-> R;
    R [ main="yes" ];
    R -[coord_fixed]-> C;
  }
  commands {
    C.main=no;
    C.recursive=yes;
  }
}
strat S1 { Try ( Iter ( Alt ( ignore_satellites_root_advmod, ignore_satellites_root_advcl, ignore_satellites_root_prepv, ignore_satellites_root_prep, ignore_satellites_root_cc, ignore_satellites_root_rcmod, ignore_satellites_root_punct, ignore_satellites_root_coord_fixed ) ) ) }
"""
```

### `grs_main_extra_in`

La estrategia *grs_main_extra_in* consta de una única regla que se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado, es decir, reescribe el grafo tantas veces como le es posible. La finalidad de la regla es, (i), localizar los subárboles con una dependencia de tipo complemento preposicional genérico (*prep* o *prepv*) que se hallen contenidos en un subárbol anotado como oración principal en términos informativos siempre que del núcleo de dicho subárbol no dependa ningún nodo con una dependencia de tipo objeto directo y, (ii), deshacer la eliminación de la anotación de dicho subárbol de tipo complemento proposicional como parte de la cláusula más relevante en términos informativos llevada a cabo por las reglas *ignore_satellites_root_prepv* y *ignore_satellites_root_prep* de la estrategia descrita previamente. Con ello se pretende mantener como integrantes de la cláusula analizada aquellos sintagmas que, a pesar de estar introducidos por preposición, se consideren argumentos y no adjuntos del verbo principal. Esta regla, sin embargo, no está exenta de la sobregeneración de anotaciones, por ejemplo en aquellos verbos intransitivos complementados por adjuntos preposiciones (como ocurre por ejemplo en la oración *Su sobrino llegó en cinco minutos*). Tampoco la estrategia de anotación seguida es, ni mucho menos, infalible, ya que en los casos en los que un objeto indirecto aparece en su forma plena, con o sin reduplicación, no se le incluirá, erróneamente, como parte de la cláusula analizada. Queda como trabajo pendiente el estudio cuantitativo del alcance de esta regla en particular y de la estrategia seguida en general.

```
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
```

### `grs_main_extra_in_sub`

La estrategia *grs_main_extra_in_sub* consta de una única regla que se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado, es decir, reescribe el grafo tantas veces como le es posible. La finalidad de la regla es análoga a la de la descrita en el párrafo inmediatamente anterior, solo que los patrones localizados deben situarse en un nivel del árbol de dependencias inferior al del nodo raíz, de tal manera que con ella se pretende gestionar la anotación de los sintagmas precedidos de preposición en las oraciones subordinadas.

```
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
```

### `grs_rheme`

La estrategia *grs_rheme* consta de una única regla que se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado, es decir, reescribe el grafo tantas veces como le es posible. La finalidad de la regla es, (i), localizar todos los subárboles dependientes del padre inmediato de un subárbol cuyo núcleo esté anotado como Tema (*theme=yes*) siempre que dichos subárboles estén anotados como parte de la cláusula más relevante informativamente y entre ellos se encuentre, al menos, con nodo con una dependencia presumiblemente argumental (esto es, distinta de *advcl*, *cc*, etc.) y, (ii), anotar como Rema (*rheme=yes*) a dicho nodo padre y a los subárboles que cumplan el patrón descrito.

```
grs_rheme = """
rule rheme {
  pattern {
    T [ theme="yes" ];
    V -> T;
    V [ theme="no", main="yes" ];
    C [ main=yes, theme="no" ];
    V -[^advcl|advmod|coord_fixed]-> C;
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
```

### `grs_rheme_cleaning`

La estrategia *grs_rheme_cleaning* contiene un total de dos reglas cuya disyunción se ejecuta de manera iterativa y devuelve el mismo grafo en el caso de no localizar el patrón declarado (es decir, mediante la estrategia anidada de las órdenes *Try*, *Iter* y *Alt*). El objetivo de ambas reglas es deshacer la anotación de Rema de los subárboles que cumplan ciertos patrones considerados inductores de sintagmas satélite. En el caso de la regla *rheme_not_punct*, el objetivo es no anotar como Rema aquellos nodos que dependen de cualquier nodo del Rema con una dependencia de tipo puntuación (*punct*). Actualmente, la versión actual del módulo no la ejecuta. En cuanto a la regla *rheme_not_rcmod*, su objetivo es no anotar como Rema aquellos subárboles cuyo núcleo dependa de cualquier nodo del Rema con una dependencia de tipo cláusula modificadora de relativo (*rcmod*).

```
grs_rheme_cleaning = """
rule rheme_not_rcmod {
  pattern {
    R [ rheme="yes" ];
    X -[^prepv|prepn]-> R;
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
strat S1 { Iter ( Try ( Alt ( rheme_not_rcmod ) ) ) }
"""
```

### `grs_rep`

Por último, Presentamos la estrategia de anotación para la proyección, de acuerdo con las decisiones del esquema de anotación:

```
grs_rep = """
rule annotated_reported_nsubj_post {
  pattern {
    X -[root]-> R;
    R -[dobj]-> O;
    O -[punct]-> P1;
    O -[punct]-> P2;
    P1 [ upos=fe ];
    P2 [ upos=fe ];
    R -[nsubj]-> SP;
    R << SP;
  }
  commands {
    SP.rep=yes;
    SP.recursive=yes;
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
strat S1 { Try ( Iter ( Alt ( annotated_reported_nsubj_post, annotated_reported_advcl, annotated_reported_advcl_bareN, annotated_reported_advcl_weirdAnn ) ) ) }
"""
```

Dicha estrategia integra varias reglas, cada una de ellas con un objetivo particular:

- La regla *annotated_reported_nsubj_post* tiene como objetivo localizar patrones en los que se incluye una porción de discurso directo seguido de un verbo de habla y anotar el sujeto de dicho verbo de habla como inductor de modalidad. Queda pendiente la definición de un lexicón de verbos de habla con que parametrizar esta regla.

- La regla *annotated_reported_advcl* tiene como objetivo localizar patrones en los que aparece una subordinada adverbial introducida por la preposición para con un objeto clausal encabezado por un verbo de habla y anotar el sujeto de dicho verbo de habla como inductor de modalidad. Queda pendiente, de nuevo, la definición de un lexicón de verbos de habla con que parametrizar esta regla.

- La regla *annotated_reported_advcl_bareN* tiene como objetivo localizar patrones en los que la preposición según introduce un sintagma nominal, que se anotará como inductor de modalidad siempre que su función no sea la complementación de modo sino la de inducción de modalidad con respecto a la oración principal. Queda pendiente la definición de un lexicón con sustantivos relativos al modo.

- La regla *annotated_reported_advcl_weirdAnn* tiene como objetivo localizar patrones que, si bien son equivalentes a los declarados en la regla *annotated_reported_advcl*, han sido anotados con un esquema de etiquetado diferente. No hemos conseguido abstraer la información que codifica este tipo de anotación con respecto a la anterior y, por ser la incidencia de este esquema notablemente inferior a la del esquema presentado anteriormente, hemos concluido que se tratan de errores de anotación.

Además, la estrategia presentada viene complementada por la siguiente:

```
grs_nsubj_ellision_rep = """
rule nsubj_ellision_rep {
  pattern {
    X -[root]-> N0;
    N0 -[nsubj]-> S;
    N0 -[dobj]-> N1;
    N1 -[cobj]-> N2;
    N2.upos = re"v.+";
  }
  without {
    N2 -[nsubj]-> S2;
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
```

El objetivo de la única regla que incluye esa última estrategia es localizar patrones en los que el verbo principal de la cláusula introducida por un verbo de habla tiene un sujeto que no se ha realizado sintácticamente en la oración y reescribir el árbol de dependencias de la oración de tal manera que, además de anotar como oración principal en términos informativos a la cláusula objeto del verbo de habla principal, el sujeto de este pasa a depender del verbo principal de dicha cláusula. Este es el caso, por ejemplo, en la oración *La empresa afirma que ha perdido más del 50 % del capital invertido por la junta a causa de la situación de emergencia internacional*, en la que el verbo *ha perdido* debe recuperar su sujeto del verbo de habla *afirma*.

Como puede observarse, la estrategia se limita a la reescritura del árbol de dependencias y deja sin anotar como inductor de modalidad al sujeto trasladado. Para mantener la simplicidad de la aplicación sucesiva de estrategias al máximo, la regla que anota como inductores de modalidad este tipo de sujetos de verbos de habla se ejecuta con anterioridad a la reescritura del árbol, de tal manera que con una sola regla es posible anotar tanto los casos en los que el verbo principal de la cláusula que introduce el verbo de habla incluyan un sujeto expreso como los casos en que este no aparezca realizado, que serán tratados posteriormente por la estrategia presentada. También con el objetivo de reducir la complejidad, y por consiguiente también el coste computacional de la aplicación sucesiva de las reglas, la estrategia de anotación de sujetos de verbos de habla como inductores de modalidad se integra en una de las estrategias encargadas de delimitar la oración principal en términos informativos que, recordemos, fueron presentadas en el módulo de las gramáticas de reescritura de árboles. La estrategia es la siguiente:

```
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
```

En concreto, la encargada de la anotación del inductor de modalidad es la regla *subordinate_dobj_clause*, cuyo objetivo es, como ya se ha adelantado, localizar patrones en los que un verbo de habla introduce una cláusula y anotar el sujeto de dicho verbo de habla como inductor de modalidad.

## 2. Estrategias para el tratamiento de la coordinación

Se ha reescrito la dependencia de la conjunción con respecto al núcleo de los coordinantes para localizarla unívocamente mediante un solo patrón. De esta manera, dependencias del tipo *dobj(comió, y)*, *coord(y, carne)*, *coord(y, pescado)* se han reescrito por estructuras equivalentes a la siguiente: *dobj(comió, carne)*, *dobj(comió, pescado)*, *coord_fixed(comió, y)*.

La estrategia llevada a cabo para generar una oración por cada coordinante, implementada en la función *coord_to_sentence*, se basa en la búsqueda de todos los subárboles mínimos que contengan una dependencia del tipo *coord_fixed* y cuyos nodos contengan el rasgo *coord* con valor “yes”. Si bien es cierto que este módulo depende de que se hayan gestionado bien este tipo de estructuras, estas suelen seguir modelos de anotación similares en los estándares de anotación automática de las herramientas más utilizadas para español, por lo que se incluye aquí una de las estrategias necesarias para lograr la estructura de datos necesaria para este módulo, en concreto la llevada a cabo para el corpus [AnCora Surface Syntax Dependencies](http://clic.ub.edu/corpus/es/ancora-descarregues)[^83] *(AnCora GLiCom-UPF 1.1*):

```
grs_dealingWith_coordination = """
rule coordinated {
  pattern {
    A -[root]-> R;
    C -[coord]-> C1;
    e: X -> C;
  }
  commands {
    del_edge C -[coord]-> C1;
    add_edge e: X -> C1;
    C1.coord=yes;
  }
}
strat S1 { Onf ( Iter ( coordinated ) ) }
"""
grs_dealingWith_coordination_root = """
rule coordinated_root {
  pattern {
    A -[root]-> X;
    C -[coord]-> C1;
    e: X -> C;
  }
  commands {
    del_edge C -[coord]-> C1;
    add_edge e: X -> C1;
    C1.coord=yes;
  }
}
strat S1 { Onf ( Iter ( coordinated_root ) ) }
"""
grs_dealingWith_coordination_ignore_cc = """
rule coordinated_ignore_cc {
  pattern {
    B [ upos=cc ];
    e: A -[^coord_fixed]-> B;
  }
  commands {
    del_edge e;
    add_edge A -[coord_fixed]-> B;
  }
}
strat S1 { Onf ( Iter ( coordinated_ignore_cc ) ) }
"""
```

Las dos primeras estrategias de anotación redirigen las dependencias de los coordinantes para hacerlos depender del núcleo de la coordinación en lugar de la conjunción. La tercera estrategia se encarga de marcar la conjunción con la dependencia *coord_fixed*, necesaria para localizar los elementos relevantes para la ejecución del módulo que nos ocupa. Debido a que estas estrategias no implican ningún tipo de anotación recursiva, es recomendable incluirlas al final de la lista de estrategias para ejecutar, ya que de lo contrario la anotación recursiva de un nodo superior podría propagar su estatus de no coordinante.

La primera estrategia diseñada para la división de la oración por coordinantes se basaba en el cálculo de la frecuencia absoluta de cada tipo de dependencia para quedarse con la de mayor frecuencia, distinta de *punct*, como la que es objeto de la coordinación. A continuación, se creaba una estructura de datos de tipo tupla con el identificador del núcleo de la coordinación como primer elemento y la dependencia coordinada como segundo elemento. Finalmente, por cada uno de los coordinantes se crea una nueva oración en la que se ha eliminado todo el subárbol que incluye la coordinación y se ha concatenado únicamente el subárbol correspondiente al coordinante del bucle en cuestión.

Sin embargo, por ser esta solución problemática en los casos en los que existen dependencias del mismo tipo que las involucradas en la coordinación que son dependientes de su mismo núcleo, se terminó por desechar esta estrategia y se asumió el coste de exigir la estructura de datos que se detalló en párrafos anteriores y que se logra fácilmente, con estrategias de anotación similares a las aportadas como ejemplo.

Un ejemplo de estructura problemática es la de la siguiente oración:

```
1	Los	el	da0mp0	da0mp0	rep=no|t=yes|r=no|m=yes|c=no	2	det
2	libros	libro	ncmp000	ncmp000	rep=no|t=yes|r=no|m=yes|c=no	5	nsubj
3	de	de	sps00	sps00	rep=no|t=yes|r=no|m=yes|c=no	2	prepn
4	texto	texto	ncms000	ncms000	rep=no|t=yes|r=no|m=yes|c=no	3	pobj
5	ofrecen	ofrecer	vmip3p0	vmip3p0	rep=no|t=no|r=yes|m=yes|c=no	0	root
6	a	a	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	5	iobj
7	los	el	da0mp0	da0mp0	rep=no|t=no|r=yes|m=yes|c=no	8	det
8	escolares	escolar	nccp000	nccp000	rep=no|t=no|r=yes|m=yes|c=no	6	pobj
9	una	uno	di0fs0	di0fs0	rep=no|t=no|r=yes|m=yes|c=no	10	det
10	visión	visión	ncfs000	ncfs000	rep=no|t=no|r=yes|m=yes|c=no	5	dobj
11	de	de	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	10	prepn
12	la	el	da0fs0	da0fs0	rep=no|t=no|r=yes|m=yes|c=no	13	det
13	historia	historia	ncfs000	ncfs000	rep=no|t=no|r=yes|m=yes|c=no	11	pobj
14	de	de	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	13	prepn
15	España	España	np00000	np00000	rep=no|t=no|r=yes|m=yes|c=no	14	pobj
16	equilibrada	equilibrado	aq0fsp	aq0fsp	rep=no|t=no|r=yes|m=yes|c=yes	10	prepn
17	,	,	fc	fc	rep=no|t=no|r=yes|m=yes|c=no	19	punct
18	universal	universal	aq0cs0	aq0cs0	rep=no|t=no|r=yes|m=yes|c=yes	10	prepn
19	y	y	cc	cc	rep=no|t=no|r=yes|m=yes|c=no	10	coord_separated
20	ajustada	ajustado	aq0fsp	aq0fsp	rep=no|t=no|r=yes|m=yes|c=yes	10	prepn
21	al	al	spcms	spcms	rep=no|t=no|r=yes|m=yes|c=no	20	oobj
22	espíritu	espíritu	ncms000	ncms000	rep=no|t=no|r=yes|m=yes|c=no	21	pobj
23	plural	plural	aq0cs0	aq0cs0	rep=no|t=no|r=yes|m=yes|c=yes	22	dep
24	y	y	cc	cc	rep=no|t=no|r=yes|m=yes|c=no	22	coord_separated
25	democrático	democrático	aq0ms0	aq0ms0	rep=no|t=no|r=yes|m=yes|c=yes	22	dep
26	inspirado	inspirado	aq0msp	aq0msp	rep=no|t=no|r=yes|m=yes|c=no	22	amod
27	en	en	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	26	oobj
28	la	el	da0fs0	da0fs0	rep=no|t=no|r=yes|m=yes|c=no	29	det
29	Constitución	Constitución	np00000	np00000	rep=no|t=no|r=yes|m=yes|c=no	27	pobj
30	de	de	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	29	prepn
31	1978	1978	z	z	rep=no|t=no|r=yes|m=yes|c=no	30	pobj
```

Como puede observarse, el sintagma *una visión de la historia de España equilibrada, universal y ajustada al espíritu plural y democrático inspirado en la Constitución de 1978* contiene los coordinantes *equilibrada*, *universal* y *ajustada*, cuyas dependencias son de tipo *prepn*, pero, de su mismo núcleo, también depende, con la misma dependencia *prepn*, el sintagma *de la historia de España*. Este, en la versión anterior del módulo, se incluiría erróneamente como uno de los elementos coordinados de la primera coordinación de la frase.

Con el nuevo enfoque propuesto, que obliga a la inclusión del nuevo rasgo *coord*, abreviado como *c*, de valor binario *yes*/*no*, es posible desambiguar la pertenencia a la estructura de coordinación de cada subárbol. Al contar esta oración con dos estructuras de coordinación, la primera con tres elementos coordinados y la segunda con dos, el número total de oraciones producidas por el módulo es de cinco:

- *Los libros de texto ofrecen a los escolares una visión de la historia de España equilibrada*.

- *Los libros de texto ofrecen a los escolares una visión de la historia de España universal*.

- *Los libros de texto ofrecen a los escolares una visión de la historia de España ajustada al espíritu plural y democrático inspirado en la Constitución de 1978*.

- *Los libros de texto ofrecen a los escolares una visión de la historia de España equilibrada , universal y ajustada al espíritu plural inspirado en la Constitución de 1978*.

- *Los libros de texto ofrecen a los escolares una visión de la historia de España equilibrada , universal y ajustada al espíritu democrático inspirado en la Constitución de 1978*.

La utilidad de este módulo, sin embargo, se justifica en mucha mayor medida por la frecuencia de la coordinación verbal y nominal en las oraciones del corpus, ya que en el caso de la coordinación de adyacentes, como es el caso en el ejemplo presentado, el aumento de la complejidad de comprensión de la oración dado por la existencia de coordinación es mucho menor. Un ejemplo de oración cuya complejidad se ve reducida notablemente gracias a la descomposición oracional que desempeña este módulo es la siguiente:

```
1	Un	uno	di0ms0	di0ms0	rep=no|t=yes|r=no|m=yes|c=no	2	det
2	informe	informe	ncms000	ncms000	rep=no|t=yes|r=no|m=yes|c=no	14	nsubj
3	de	de	sps00	sps00	rep=no|t=yes|r=no|m=yes|c=no	2	prepn
4	la	el	da0fs0	da0fs0	rep=no|t=yes|r=no|m=yes|c=no	5	det
5	Real	real	ncfp000	ncfp000	rep=no|t=yes|r=no|m=yes|c=no	3	pobj
6	Academia	academia	ncfp000	ncfp000	rep=no|t=yes|r=no|m=yes|c=no	5	appos
7	de	de	sps00	sps00	rep=no|t=yes|r=no|m=yes|c=no	5	prepn
8	la	el	da0fs0	da0fs0	rep=no|t=yes|r=no|m=yes|c=no	9	det
9	Historia	Historia	np00000	np00000	rep=no|t=yes|r=no|m=yes|c=no	7	pobj
10	hecho	hecho	aq0msp	aq0msp	rep=no|t=yes|r=no|m=yes|c=no	2	amod
11	público	público	aq0ms0	aq0ms0	rep=no|t=yes|r=no|m=yes|c=no	10	amod
12	esta	este	dd0fs0	dd0fs0	rep=no|t=yes|r=no|m=yes|c=no	13	det
13	semana	semana	ncfs000	ncfs000	rep=no|t=yes|r=no|m=yes|c=no	10	tmod
14	acusó	acusar	vmis3s0	vmis3s0	rep=no|t=no|r=yes|m=yes|c=no	0	root
15	a	a	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	14	dobj
16	las	el	da0fp0	da0fp0	rep=no|t=no|r=yes|m=yes|c=no	17	det
17	comunidades	comunidad	ncfp000	ncfp000	rep=no|t=no|r=yes|m=yes|c=no	15	pobj
18	autónomas	autónomo	aq0fp0	aq0fp0	rep=no|t=no|r=yes|m=yes|c=no	17	amod
19	de	de	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	14	oobj
20	&quot;	&quot;	fe	fe	rep=no|t=no|r=yes|m=yes|c=no	21	punct
21	tergiversar	tergiversar	vmn0000	vmn0000	rep=no|t=no|r=yes|m=yes|c=yes	19	pobj
22	&quot;	&quot;	fe	fe	rep=no|t=no|r=yes|m=yes|c=no	21	punct
23	la	el	da0fs0	da0fs0	rep=no|t=no|r=yes|m=yes|c=no	24	det
24	enseñanza	enseñanza	ncfs000	ncfs000	rep=no|t=no|r=yes|m=yes|c=no	21	dobj
25	de	de	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	24	prepn
26	esta	este	dd0fs0	dd0fs0	rep=no|t=no|r=yes|m=yes|c=no	27	det
27	disciplina	disciplina	ncfs000	ncfs000	rep=no|t=no|r=yes|m=yes|c=no	25	pobj
28	,	,	fc	fc	rep=no|t=no|r=yes|m=yes|c=no	29	punct
29	y	y	cc	cc	rep=no|t=no|r=yes|m=yes|c=no	19	coord_separated
30	convertirla	convertir	vmn0000	vmn0000	rep=no|t=no|r=yes|m=yes|c=yes	19	pobj
31	en	en	sps00	sps00	rep=no|t=no|r=yes|m=yes|c=no	30	oobj
32	&quot;	&quot;	fe	fe	rep=no|t=no|r=yes|m=yes|c=no	34	punct
33	una	uno	di0fs0	di0fs0	rep=no|t=no|r=yes|m=yes|c=no	34	det
34	historia	historia	ncfs000	ncfs000	rep=no|t=no|r=yes|m=yes|c=no	31	pobj
35	local	local	aq0cs0	aq0cs0	rep=no|t=no|r=yes|m=yes|c=yes	34	dep
36	,	,	fc	fc	rep=no|t=no|r=yes|m=yes|c=no	38	punct
37	discontinua	discontinuo	aq0fs0	aq0fs0	rep=no|t=no|r=yes|m=yes|c=yes	34	dep
38	y	y	cc	cc	rep=no|t=no|r=yes|m=yes|c=no	34	coord_separated
39	particularista	particularista	aq0cs0	aq0cs0	rep=no|t=no|r=yes|m=yes|c=yes	34	dep
40	&quot;	&quot;	fe	fe	rep=no|t=no|r=yes|m=yes|c=no	34	punct
```

Gracias a este módulo, la oración *Un informe de la Real Academia de la Historia hecho público esta semana acusó a las comunidades autónomas , en particular a Catalunya , el País Vasco y Galicia , de "tergiversar" la enseñanza de esta disciplina , y convertirla en "una historia local , discontinua y particularista"* se divide en las dos oraciones siguientes:

- *Un informe de la Real Academia de la Historia hecho público esta semana acusó a las comunidades autónomas, en particular a Catalunya, el País Vasco y Galicia, de "tergiversar " la enseñanza de esta disciplina*.

- *Un informe de la Real Academia de la Historia hecho público esta semana acusó a las comunidades autónomas, en particular a Catalunya, el País Vasco y Galicia, de convertirla en " una historia local , discontinua y particularista"*.

Debe notarse, sin embargo, que este enfoque de simplificación oracional se topa con otro problema: el de la muy frecuente elisión de complementos cuando la coordinación tiene lugar entre verbos. Este asunto, cuya solución no es en absoluto sencilla, está siendo analizado con la vista puesta en la automatización de la resolución de elisiones. En el caso de las elisiones de sujetos antepuestos, especialmente relevantes para nuestro modelo, la resolución de la elisión suele resolverse recuperando el sujeto de la oración anterior siempre que este concuerde en número con el verbo coordinado. Queda, sin embargo, pendiente realizar un estudio de las métricas de rendimiento de esta estrategia sobre un conjunto representativo del corpus.

Por el momento, la salida de este módulo no se ha empleado como entrada del módulo siguiente por seguir en desarrollo, pero la idea es que, efectivamente, actúe como un módulo de procesamiento intermedio entre la salida del módulo de reescritura de árboles y el de anotación automática de roles semánticos. La motivación de su diseño viene dada por el hecho de que el problema de la complejidad de la coordinación empeora en gran medida el rendimiento del anotador automático de roles semánticos.

### Funciones auxiliares

Cabe destacar que, para la implementación de este módulo, se han definido una serie de funciones de gran utilidad para diversas tareas genéricas de tratamiento de ficheros CoNLL-U:

- La función *search_id* recibe como argumentos una cadena que puede estar compuesta de varias palabras y una oración en formato CoNLL-U y devuelve una lista con los identificadores de las palabras correspondientes a la cadena de entrada en la oración, siempre que los encuentre de manera consecutiva —esto es, literalmente teniendo en cuenta el orden lineal—. La estrategia para lograr este objetivo consiste en la creación de una lista en la que se almacenan los identificadores de las palabras encontradas para cada palabra en la oración y la gestión del particular en el que la longitud de dicha lista sea mayor que el número de palabras de la cadena del primer argumento de la función. Dicho particular es muy frecuente, especialmente cuando en la cadena aparecen palabras funcionales como determinantes o preposiciones, cuya frecuencia de aparición en las oraciones es relativamente alta y no es raro que aparezcan más de una vez en una misma oración. En dicho particular, la función se encarga de recorrer la lista generada y, para cada elemento, calcular el identificador siguiente y comprobar si efectivamente se encuentra en el resto de la lista. En el caso de que el identificador siguiente no se encuentre en el resto de la lista, se borra el elemento actual de la lista generada. En el caso de que el identificador efectivamente se encuentre en alguna posición del resto de la lista a partir del elemento que se esté examinando, se eliminan los identificadores situados entre dicho elemento examinado y el que contiene el identificador siguiente y se continúa evaluando la lista a partir del identificador siguiente.

  Como ejemplo de ejecución de esta función, veamos el caso de la llamada con una cadena *en la Constitución de* y una oración como la siguiente:

```
1	Los	el	da0mp0	da0mp0	2	det
2	libros	libro	ncmp000	ncmp000	5	nsubj
3	de	de	sps00	sps00	2	prepn
4	texto	texto	ncms000	ncms000	3	pobj
5	ofrecen	ofrecer	vmip3p0	vmip3p0	0	root
6	a	a	sps00	sps00	5	iobj
7	los	el	da0mp0	da0mp0	8	det
8	escolares	escolar	nccp000	nccp000	6	pobj
9	una	uno	di0fs0	di0fs0	10	det
10	visión	visión	ncfs000	ncfs000	5	dobj
11	de	de	sps00	sps00	10	prepn
12	la	el	da0fs0	da0fs0	13	det
13	historia	historia	ncfs000	ncfs000	11	pobj
14	de	de	sps00	sps00	13	prepn
15	España	España	np00000	np00000	14	pobj
16	equilibrada	equilibrado	aq0fsp	aq0fsp	10	prepn
17	,	,	fc	fc	19	punct
18	universal	universal	aq0cs0	aq0cs0	10	prepn
19	y	y	cc	cc	10	coord_fixed
20	ajustada	ajustado	aq0fsp	aq0fsp	10	prepn
21	al	al	spcms	spcms	20	oobj
22	espíritu	espíritu	ncms000	ncms000	21	pobj
23	plural	plural	aq0cs0	aq0cs0	22	dep
24	y	y	cc	cc	22	coord_fixed
25	democrático	democrático	aq0ms0	aq0ms0	22	dep
26	inspirado	inspirado	aq0msp	aq0msp	22	amod
27	en	en	sps00	sps00	26	oobj
28	la	el	da0fs0	da0fs0	29	det
29	Constitución	Constitución	np00000	np00000	27	pobj
30	de	de	sps00	sps00	29	prepn
31	1978	1978	z	z	30	pobj
```

La lista generada con los identificadores encontrados para cada palabra es *['27', '12', '28', '29', '3', '11', '14', '30']*. Como puede observarse, su longitud —8— es mayor que el número de palabras de la cadena de entrada —4—. Esto se debe a que la segunda palabra de la cadena —*la*— se encuentra en varias posiciones de la oración —concretamente en la 12 y en la 28—. Lo mismo ocurre con la última palabra de la cadena del primer argumento —*de*—, que aparece también varias veces en la oración —concretamente cuatro veces, con los identificadores 3, 11, 14 y 30—. La estrategia desarrollada comienza examinando el primer elemento de la lista —27— y, como encuentra a su sucesor en el resto de la lista —concretamente en la tercera posición—, mantiene dicho elemento, borra los elementos que ha desechado entre medias y sigue examinando la lista a partir de la posición del mismo. Tiene éxito a la hora de localizar al siguiente sucesor —29—, que sucede inmediatamente al elemento examinado, por lo que no tiene lugar el borrado de ningún elemento. El último sucesor antes de que la longitud de la lista generada alcance el número exacto de palabras en la cadena de entrada sí causa el borrado de los elementos intermedios entre este y su antecesor —es decir, 3, 11 y 14—. La salida de la función, por tanto, sería finalmente *'27', '28', '29', 30']*.

- La función *keep_annotations* recibe como primer argumento una lista de rasgos y como segundo argumento una oración y devuelve una nueva oración compuesta por aquellos nodos de la oración que recibe como argumento que contengan el valor “yes” en alguno de los rasgos de la lista que recibe como primer argumento. La estrategia seguida para ello gestiona aquellos casos en los que el subárbol seleccionado no contenga el nodo raíz del árbol, de tal manera que analiza recursivamente los subárboles hijos a partir del nodo raíz hasta encontrar el primero que contenga uno de los rasgos indicados en el primer argumento. Una vez encontrado el nodo superior que cumpla con los requisitos descritos, se establece como nuevo nodo raíz, de manera que la salida de la función continúa cumpliendo los requisitos para considerarse un grafo de tipo árbol.

- La función *reset_ids* toma como argumento una oración en formato CoNLL-U y devuelve la misma oración en el mismo formato reescribiendo los identificadores de sus palabras, así como los identificadores de los núcleos de las dependencias de los mismos, de tal manera que comiencen por el número uno y vayan incrementando en una unidad por palabra. La funcionalidad que aporta es necesaria para mantener el formato de datos CoNLL-U recomendado y, en nuestro módulo, suele ejecutarse, normalmente, a continuación de la función *keep_annotations*. Para no aumentar innecesariamente el coste de procesamiento del módulo, la funcionalidad que aporta se ha programado de manera independiente con respecto a la función *keep_annotations*, ya que puede darse el caso de que se aplique varias veces la función *keep_annotations* en una determinada estrategia de procesamiento de datos y basta con ejecutar una vez la funcionalidad de *reset_ids* para que la oración mantenga el orden lineal en cuanto a sus identificadores.

- La función *rewrite_dep* toma como primer argumento el identificador de una palabra, como segundo argumento el identificador de otra palabra, como tercer argumento el nombre de un tipo de dependencia y como cuarto argumento una oración en formato CoNLL-U. Devuelve una nueva oración en formato CoNLL-U en la que la palabra identificada por el número del segundo argumento tiene como núcleo, de una dependencia del tipo indicado en el tercer argumento, a la palabra identificada por el número del primer argumento.

- La función *get_sons_ids* toma como primer argumento el identificador de una palabra y como segundo argumento una oración en formato CoNLL-U. Devuelve una lista de los identificadores correspondientes a las palabras que dependen inmediatamente de la palabra cuyo identificador se aporta en el primer argumento en la oración del segundo argumento.
