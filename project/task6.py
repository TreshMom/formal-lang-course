import networkx as nx
import pyformlang
from typing import Tuple

from pyformlang.cfg import CFG, Variable, Terminal, Epsilon


def cfg_to_weak_normal_form(cfg: CFG) -> CFG:
    clear_cfg = cfg.eliminate_unit_productions().remove_useless_symbols()
    decomposed = clear_cfg._decompose_productions(
        clear_cfg._get_productions_with_only_single_terminals()
    )
    return CFG(productions=set(decomposed), start_symbol=Variable("S"))


def cfpq_with_hellings(
    cfg: CFG,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[Tuple[int, int]]:

    if start_nodes is None:
        start_nodes = set(graph.nodes)
    if final_nodes is None:
        final_nodes = set(graph.nodes)

    cfg_weak = cfg_to_weak_normal_form(cfg)

    cfg_ones = {}
    cfg_twos = set()
    cfg_threes = {}

    for p in cfg_weak.productions:
        p_len = len(p.body)
        if p_len == 1 and isinstance(p.body[0], Terminal):
            cfg_ones.setdefault(p.head, set()).add(p.body[0])
        elif p_len == 1 and isinstance(p.body[0], Epsilon):
            cfg_twos.add(p.head)
        elif p_len == 2:
            cfg_threes.setdefault(p.head, set()).add((p.body[0], p.body[1]))

    result = {(n_ith, vert, vert) for n_ith in cfg_twos for vert in graph.nodes}
    for v, u, tag in graph.edges.data("label"):
        for n_ith in cfg_ones:
            if tag in cfg_ones[n_ith]:
                result.add((n_ith, v, u))
    immediate = result.copy()

    while len(immediate) > 0:
        n_ith, vi, ui = immediate.pop()
        add_to = set()
        for n_jth, vj, uj in result:
            if vi == ui:
                for n_kth in cfg_threes:
                    if (n_jth, n_ith) in cfg_threes[n_kth] and (
                        n_kth,
                        vj,
                        ui,
                    ) not in result:
                        immediate.add((n_kth, vj, ui))
                        add_to.add((n_kth, vj, ui))
            if ui == vi:
                for n_kth in cfg_threes:
                    if (n_ith, n_jth) in cfg_threes[n_kth] and (
                        n_kth,
                        vi,
                        uj,
                    ) not in result:
                        immediate.add((n_kth, vi, uj))
                        add_to.add((n_kth, vi, uj))
        result.update(add_to)

    final_result = {
        (v, u)
        for n_ith, v, u in result
        if v in start_nodes and u in final_nodes and n_ith == cfg.start_symbol.value
    }

    return final_result
