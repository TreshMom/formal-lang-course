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

from pyformlang.cfg import CFG
from collections import defaultdict
from collections import deque
from typing import Deque
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple

import pyformlang
import networkx as nx


def cfg_to_weak_normal_form(cfg: CFG) -> CFG:
    cfg1 = cfg.eliminate_unit_productions().remove_useless_symbols()
    tmp = cfg1._get_productions_with_only_single_terminals()
    new_prod = cfg1._decompose_productions(tmp)
    return CFG(start_symbol=cfg1.start_symbol, productions=new_prod)


def cfg_from_file(path: str) -> CFG:
    with open(path) as f:
        return CFG.from_text(f.read())


def _cfpq_with_hellings(
    cfg: pyformlang.cfg.CFG, graph: nx.DiGraph
) -> Set[Tuple[int, pyformlang.cfg.Variable, int]]:
    cfg = cfg_to_weak_normal_form(cfg)

    var_production_body_to_head: Dict[
        Tuple[pyformlang.cfg.Variable, pyformlang.cfg.Variable],
        Set[pyformlang.cfg.Variable],
    ] = defaultdict(set)

    result: Set[Tuple[int, pyformlang.cfg.Variable, int]] = set()

    # dictionaries letting to iterate over `result` elements
    # with specified first or last component
    start_to_var_and_finish_pairs: Dict[
        int, Set[Tuple[pyformlang.cfg.Variable, int]]
    ] = defaultdict(set)
    finish_to_start_and_var_pairs: Dict[
        int, Set[Tuple[int, pyformlang.cfg.Variable]]
    ] = defaultdict(set)

    unhandled: Deque[Tuple[int, pyformlang.cfg.Variable, int]] = deque()

    def register_reachability(start, var, finish):
        triple = (start, var, finish)
        if triple not in result:
            result.add(triple)
            unhandled.append(triple)
            start_to_var_and_finish_pairs[start].add((var, finish))
            finish_to_start_and_var_pairs[finish].add((start, var))

    edges_grouped_by_label: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    for start, finish, attributes in graph.edges.data():
        edges_grouped_by_label[attributes["label"]].append((start, finish))

    for production in cfg.productions:
        match production.body:
            case [] | [pyformlang.cfg.Epsilon()]:
                for node in graph.nodes:
                    register_reachability(node, production.head, node)
            case [pyformlang.cfg.Terminal() as terminal]:
                for start, finish in edges_grouped_by_label[terminal.value]:
                    register_reachability(start, production.head, finish)
            case [pyformlang.cfg.Variable() as var1, pyformlang.cfg.Variable() as var2]:
                var_production_body_to_head[(var1, var2)].add(production.head)

    while unhandled:
        (node1, var1, node2) = unhandled.popleft()
        for start, var, finish in [
            (node0, var, node2)
            for (node0, var0) in finish_to_start_and_var_pairs[node1]
            for var in var_production_body_to_head[(var0, var1)]
        ] + [
            (node1, var, node3)
            for (var2, node3) in start_to_var_and_finish_pairs[node2]
            for var in var_production_body_to_head[(var1, var2)]
        ]:
            register_reachability(start, var, finish)
    return result


def cfpq_with_hellings(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> set[Tuple[int, int]]:
    return {
        (start, finish)
        for (start, var, finish) in _cfpq_with_hellings(cfg, graph)
        if var == cfg.start_symbol
        and (start_nodes is None or start in start_nodes)
        and (final_nodes is None or finish in final_nodes)
        and start != finish
    }
