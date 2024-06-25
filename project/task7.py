import pyformlang
from pyformlang.cfg import Terminal
from scipy.sparse import dok_matrix

import networkx as nx
from typing import *

import copy

from project.task6 import cfg_to_weak_normal_form


def cfpq_with_matrix(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> set[tuple[int, int]]:

    start_nodes = graph.nodes if start_nodes is None else start_nodes
    final_nodes = graph.nodes if final_nodes is None else final_nodes
    cfg = cfg_to_weak_normal_form(cfg)

    M = {
        p.head.to_text(): dok_matrix(
            (graph.number_of_nodes(), graph.number_of_nodes()), dtype=bool
        )
        for p in cfg.productions
    }

    t_to_Ts = {}
    for p in cfg.productions:
        if len(p.body) == 1 and isinstance(p.body[0], Terminal):
            t_to_Ts.setdefault(p.body[0].to_text(), set()).add(p.head.to_text())

    for b, e, t in graph.edges(data="label"):
        if t in t_to_Ts:
            for T in t_to_Ts[t]:
                M[T][b, e] = True

    N_to_eps = {p.head.to_text() for p in cfg.productions if len(p.body) == 0}
    for N in N_to_eps:
        M[N].setdiag(True)

    M_new = copy.deepcopy(M)
    for m in M_new.values():
        m.clear()

    N_to_NN = {}
    for p in cfg.productions:
        if len(p.body) == 2:
            N_to_NN.setdefault(p.head.to_text(), set()).add(
                (p.body[0].to_text(), p.body[1].to_text())
            )

    for j in range(graph.number_of_nodes() ** 2):
        for N, NN in N_to_NN.items():
            for Nl, Nr in NN:
                M_new[N] += M[Nl] @ M[Nr]
        for N, m in M_new.items():
            M[N] += m

    S = cfg.start_symbol.to_text()
    ns, ms = M[S].nonzero()
    return {(n, m) for n, m in zip(ns, ms) if n in start_nodes and m in final_nodes}
