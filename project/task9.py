from project.task8 import cfg_to_rsm

from pyformlang.rsa import RecursiveAutomaton
from pyformlang.cfg import CFG
from pyformlang.finite_automaton import State, Symbol

import networkx as nx

from copy import deepcopy


def cfpq_with_gll(
    cfg_or_rsm: CFG | RecursiveAutomaton,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:

    rsm = (
        cfg_or_rsm
        if isinstance(cfg_or_rsm, RecursiveAutomaton)
        else cfg_to_rsm(cfg_or_rsm)
    )

    start_nodes = graph.nodes if start_nodes is None else start_nodes
    final_nodes = graph.nodes if final_nodes is None else final_nodes

    rsm_start_nonterminal = rsm.initial_label.value

    stack_start_states = {
        (rsm_start_nonterminal, start_node) for start_node in start_nodes
    }
    stack_graph = {st: set() for st in stack_start_states}

    rsm_start_state = rsm.boxes[rsm.initial_label].dfa.start_state.value
    visited = {
        ((rsm_start_nonterminal, rsm_start_state), st[1], st)
        for st in stack_start_states
    }
    to_visit = deepcopy(visited)

    popped = {}
    res = set()

    while len(to_visit) != 0:
        rsm_state, graph_node, stack_state = to_visit.pop()

        if State(rsm_state[1]) in rsm.boxes[rsm_state[0]].dfa.final_states:
            if stack_state in stack_start_states:
                if graph_node in final_nodes:
                    res.add((stack_state[1], graph_node))

            popped.setdefault(stack_state, set()).add(graph_node)
            for to_stack_state, to_rsm_state in stack_graph.setdefault(
                stack_state, set()
            ):
                new_state = (to_rsm_state, graph_node, to_stack_state)
                if new_state not in visited:
                    to_visit.add(new_state)
                    visited.add(new_state)

        to_nodes = {}
        for _, n, l in graph.edges(graph_node, data="label"):
            to_nodes.setdefault(l, set()).add(n)

        dfa_dict = rsm.boxes[Symbol(rsm_state[0])].dfa.to_dict()
        if State(rsm_state[1]) not in dfa_dict:
            continue
        for symbol, to in dfa_dict[State(rsm_state[1])].items():
            if symbol in rsm.labels:
                new_stack_state = (symbol.value, graph_node)
                if new_stack_state in popped:
                    for to_graph_node in popped[new_stack_state]:
                        new_state = (
                            (rsm_state[0], to.value),
                            to_graph_node,
                            stack_state,
                        )
                        if new_state not in visited:
                            to_visit.add(new_state)
                            visited.add(new_state)
                stack_graph.setdefault(new_stack_state, set()).add(
                    (stack_state, (rsm_state[0], to.value))
                )
                start_state = rsm.boxes[symbol].dfa.start_state.value
                new_state = ((symbol.value, start_state), graph_node, new_stack_state)
                if new_state not in visited:
                    to_visit.add(new_state)
                    visited.add(new_state)
            else:
                if symbol.value not in to_nodes:
                    continue
                for node in to_nodes[symbol.value]:
                    new_state = ((rsm_state[0], to.value), node, stack_state)
                    if new_state not in visited:
                        to_visit.add(new_state)
                        visited.add(new_state)
    return res
