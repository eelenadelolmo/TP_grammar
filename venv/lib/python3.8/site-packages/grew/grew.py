"""
Grew module : anything you want to talk about graphs
Graphs are represented either by a dict (called dict-graph),
or by an str (str-graph).
"""
import os.path
import re
import copy
import tempfile
import json

from grew import network
from grew import utils

''' Library tools '''

def init():
    """
    Initialize connection to GREW library
    :return: True if anything went right
    """
    return network.init()

def grs(grsystem):
    """Load a grs stored in a file
    :param grs: either a file name or a GREW string representation of a grs
    :raise an error if the file was not correctly loaded
    """
    try:
        if os.path.isfile(grsystem):
            req = { "command": "load_grs", "filename": grsystem }
            reply = network.send_and_receive(req)
        else:
            with tempfile.NamedTemporaryFile(mode="w", delete=True, suffix=".grs") as f:
                f.write(grsystem)
                f.seek(0)  # to be read by others
                req = { "command": "load_grs", "filename": f.name }
                reply = network.send_and_receive(req)
        return reply["index"]
    except:
        raise utils.GrewError("Could not build a GRS with: %s" % grsystem)

def run(rs, gr, strat="main"):
    """
    Apply rs or the last loaded one to [gr]
    :param gr: the graph, either a str (in grew format) or a dict
    :param rs: a graph rewriting system or a GREW string representation of a grs
    :param strategy: the strategy. By default, !
    :return: the list of rewritten graphs
    """
    if isinstance(rs, int):
        index=rs
    else:
        index = grs(rs)

    req = {
        "command": "run",
        "graph": json.dumps(gr),
        "grs_index": index,
        "strat": strat
    }
    reply = network.send_and_receive(req)
    return utils.rm_dups(reply)

def corpus(data):
    """Load a corpus from a file of a string
    :param grs: either a file name or a CoNLL string representation of a corpus
    :raise an error if the file was not correctly loaded
    """
    try:
        if os.path.isfile(data):
            req = { "command": "load_corpus", "files": [data] }
            reply = network.send_and_receive(req)
        else:
            with tempfile.NamedTemporaryFile(mode="w", delete=True, suffix=".conll") as f:
                f.write(data)
                f.seek(0)  # to be read by others
                req = { "command": "load_corpus", "filename": f.name }
                reply = network.send_and_receive(req)
        return reply["index"]
    except:
        raise utils.GrewError("Could not build a corpus with: %s" % data)

def search(pattern, gr):
    """
    Search for [pattern] into [gr]
    :param patten: a string pattern
    :param gr: the graph
    :return: the list of matching of [pattern] into [gr]
    """
    req = {
        "command": "search",
        "graph": json.dumps(gr),
        "pattern": pattern
    }
    reply = network.send_and_receive(req)
    return reply

def corpus_search(pattern, corpus_index):
    """
    Search for [pattern] into [corpus_index]
    :param patten: a string pattern
    :param corpus_index: an integer given by the [corpus] function
    :return: the list of matching of [pattern] into the corpus
    """
    req = {
        "command": "corpus_search",
        "corpus_index": corpus_index,
        "pattern": pattern
    }
    reply = network.send_and_receive(req)
    return reply


def json_grs(rs):
    req = { "command": "json_grs", "grs_index": rs }
    return network.send_and_receive(req)


