import networkx as nx
import pyformlang
from pyformlang.cfg import Epsilon
from pyformlang.finite_automaton import State, Symbol
from pyformlang.regular_expression import Regex
from pyformlang.rsa import Box
from scipy.sparse import dok_matrix, eye

from project.task2 import graph_to_nfa
from project.task3 import (
    FiniteAutomaton,
    nfa_to_matrix,
    make_transitive_closure,
    intersect_automata,
)


def cfpq_with_tensor(
    rsm: pyformlang.rsa.RecursiveAutomaton,
    graph: nx.DiGraph,
    final_nodes: set[int] = None,
    start_nodes: set[int] = None,
) -> set[tuple[int, int]]:

    rsm_mat, eps_states = rsm_to_mat_with_epsilons(rsm)
    graph_mat = nfa_to_matrix(graph_to_nfa(graph, start_nodes, final_nodes))
    rsm_ids = rsm_mat.indices()
    graph_ids = graph_mat.indices()

    num_states = graph_mat.states_count

    for var in eps_states:
        if var not in graph_mat.m:
            graph_mat.m[var] = dok_matrix((num_states, num_states), dtype=bool)
        graph_mat.m[var] += eye(num_states, dtype=bool)

    last_nnz: int = 0

    while True:
        closure = make_transitive_closure(
            intersect_automata(rsm_mat, graph_mat)
        ).nonzero()
        closure = list(zip(*closure))

        nnz_count = len(closure)
        if nnz_count == last_nnz:
            break
        last_nnz = nnz_count

        for i, j in closure:
            src = rsm_ids[i // num_states]
            dst = rsm_ids[j // num_states]

            if src in rsm_mat.start and dst in rsm_mat.final:
                var = src.value[0]
                if var not in graph_mat.m:
                    graph_mat.m[var] = dok_matrix((num_states, num_states), dtype=bool)
                graph_mat.m[var][i % num_states, j % num_states] = True

    result: set[tuple[int, int]] = set()
    for _, m in graph_mat.m.items():
        for i, j in zip(*m.nonzero()):
            if graph_ids[i] in rsm_mat.start and graph_ids[j] in rsm_mat.final:
                result.add((graph_ids[i], graph_ids[j]))

    return result


def cfg_to_rsm(cfg: pyformlang.cfg.CFG) -> pyformlang.rsa.RecursiveAutomaton:
    prods = dict()
    for p in cfg.productions:
        if len(p.body) == 0:
            regex = Regex(
                " ".join(
                    "$" if isinstance(var, Epsilon) else var.value for var in p.body
                )
            )
        else:
            regex = Regex("$")
        if Symbol(p.head) not in prods:
            prods[Symbol(p.head)] = regex
        else:
            prods[Symbol(p.head)] = prods[Symbol(p.head)].union(regex)

    result = dict()

    for var, regex in prods.items():
        result[Symbol(var)] = Box(
            regex.to_epsilon_nfa().to_deterministic(), Symbol(var)
        )

    return pyformlang.rsa.RecursiveAutomaton(
        set(result.keys()), Symbol("S"), set(result.values())
    )


def ebnf_to_rsm(ebnf: str) -> pyformlang.rsa.RecursiveAutomaton:
    prods = dict()

    for p in ebnf.splitlines():
        p = p.strip()
        if "->" not in p:
            continue

        head, body = p.split("->")
        head = head.strip()
        body = body.strip() if body.strip() != "" else Epsilon().to_text()

        if head in prods:
            prods[head] += " | " + body
        else:
            prods[head] = body

    result = dict()
    for var, regex in prods.items():
        result[Symbol(var)] = Box(
            Regex(regex).to_epsilon_nfa().to_deterministic(), Symbol(var)
        )

    return pyformlang.rsa.RecursiveAutomaton(
        set(result.keys()), Symbol("S"), set(result.values())
    )


def rsm_to_mat_with_epsilons(
    rsm: pyformlang.rsa.RecursiveAutomaton,
) -> (FiniteAutomaton, set[Epsilon]):
    all_states = set()
    start_states = set()
    final_states = set()
    epsilon_symbols = set()

    for var, p in rsm.boxes.items():
        for state in p.dfa.states:
            s = State((var, state.value))
            all_states.add(s)
            if state in p.dfa.start_states:
                start_states.add(s)
            if state in p.dfa.final_states:
                final_states.add(s)

    mapping = dict()
    for i, v in enumerate(sorted(all_states, key=lambda x: x.value[1])):
        mapping[v] = i

    def to_set(o):
        if not isinstance(o, set):
            return {o}
        return o

    m = dict()
    states_len = len(all_states)
    for var, p in rsm.boxes.items():
        for src, transition in p.dfa.to_dict().items():
            for symbol, dst in transition.items():
                label = symbol.value
                if symbol not in m:
                    m[label] = dok_matrix((states_len, states_len), dtype=bool)
                for target in to_set(dst):
                    m[label][
                        mapping[State((var, src.value))],
                        mapping[State((var, target.value))],
                    ] = True
                if isinstance(dst, Epsilon):
                    epsilon_symbols.add(label)

    result = FiniteAutomaton(m, start_states, final_states, mapping)
    result.states_count = states_len
    return result, epsilon_symbols
