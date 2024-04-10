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
