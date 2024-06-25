from itertools import product
from typing import Set, Tuple, Union

import networkx as nx
from pyformlang.cfg import CFG, Epsilon
from pyformlang.finite_automaton import EpsilonNFA, Symbol, State, TransitionFunction
from pyformlang.regular_expression import Regex
from pyformlang.rsa import RecursiveAutomaton, Box
from scipy.sparse import dok_matrix, kron, eye, csr_matrix

from project.task2 import graph_to_nfa


def cfpq_with_tensor(
    cfg_or_rsm: Union[CFG, RecursiveAutomaton],
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> Set[Tuple[int, int]]:

    rsm = (
        cfg_or_rsm
        if isinstance(cfg_or_rsm, RecursiveAutomaton)
        else cfg_to_rsm(cfg_or_rsm)
    )

    start_nodes = graph.nodes if start_nodes is None else start_nodes
    final_nodes = graph.nodes if final_nodes is None else final_nodes

    rsm_states = [
        (N.value, state.value)
        for N, box in rsm.boxes.items()
        for state in box.dfa.states
    ]
    rsm_state_to_idx = {state: i for i, state in enumerate(rsm_states)}

    rsm_start_states = {
        (N.value, start_state.value)
        for N, box in rsm.boxes.items()
        for start_state in box.dfa.start_states
    }

    rsm_final_states = {
        (N.value, final_state.value)
        for N, box in rsm.boxes.items()
        for final_state in box.dfa.final_states
    }

    rsm_mat = {}
    for N, box in rsm.boxes.items():
        for from_state, transitions in box.dfa.to_dict().items():
            for symbol, to_state in transitions.items():
                from_idx = rsm_state_to_idx[(N.value, from_state.value)]
                to_idx = rsm_state_to_idx[(N.value, to_state.value)]
                rsm_mat.setdefault(
                    symbol.value,
                    dok_matrix((len(rsm_states), len(rsm_states)), dtype=bool),
                )[from_idx, to_idx] = True

    graph_nfa = graph_to_nfa(graph, start_nodes, final_nodes)
    graph_states = [state.value for state in graph_nfa.states]
    graph_state_to_idx = {state: i for i, state in enumerate(graph_states)}
    graph_mat = {}
    for from_state, transitions in graph_nfa.to_dict().items():
        for symbol, to_states in transitions.items():
            if not isinstance(to_states, set):
                to_states = {to_states}
            for to_state in to_states:
                from_idx = graph_state_to_idx[from_state.value]
                to_idx = graph_state_to_idx[to_state.value]
                graph_mat.setdefault(
                    symbol.value,
                    dok_matrix((len(graph_states), len(graph_states)), dtype=bool),
                )[from_idx, to_idx] = True

    idx_to_state = {
        i: state for i, state in enumerate(product(graph_states, rsm_states))
    }

    n_nonzero = 0
    while True:
        n_rsm_states = len(rsm_states)
        n_graph_states = len(graph_nfa.states)
        n = n_rsm_states * n_graph_states
        symbols = rsm_mat.keys() & graph_mat.keys()
        if symbols:
            mat = {
                symbol: kron(graph_mat[symbol], rsm_mat[symbol]) for symbol in symbols
            }
            m = sum(mat.values())
        else:
            m = dok_matrix((n, n), dtype=bool)
        m += eye(n, dtype=bool)

        for _ in range(n):
            m += m @ m
        new_n_nonzero = m.count_nonzero()
        if new_n_nonzero <= n_nonzero:
            break
        else:
            n_nonzero = new_n_nonzero

        for from_idx, to_idx in zip(*m.nonzero()):
            from_state = idx_to_state[from_idx]
            to_state = idx_to_state[to_idx]
            from_rsm_state = from_state[1]
            to_rsm_state = to_state[1]
            if from_rsm_state in rsm_start_states and to_rsm_state in rsm_final_states:
                N = from_rsm_state[0]
                from_graph_idx = graph_state_to_idx[from_state[0]]
                to_graph_idx = graph_state_to_idx[to_state[0]]
                graph_mat.setdefault(
                    N, dok_matrix((len(graph_states), len(graph_states)), dtype=bool)
                )[from_graph_idx, to_graph_idx] = True

    S = rsm.initial_label.value
    if S not in graph_mat:
        return set()

    res = set()
    for from_graph_state, to_graph_state in product(start_nodes, final_nodes):
        if graph_mat[S][
            graph_state_to_idx[from_graph_state], graph_state_to_idx[to_graph_state]
        ]:
            res.add((from_graph_state, to_graph_state))
    return res


def cfg_to_rsm(cfg: CFG) -> RecursiveAutomaton:
    states = {}
    symbols = {}
    start_states = {}
    final_states = {}
    transition_functions = {}

    for p in cfg.productions:
        N = p.head
        init = len(states.setdefault(N, set()))
        states[N].add(State(init))
        i = init
        for t in p.body:
            s = State(i)
            e = State(i + 1)
            symbol = Symbol(t.to_text())
            states[N].add(e)
            symbols.setdefault(N, set()).add(symbol)
            transition_functions.setdefault(N, TransitionFunction()).add_transition(
                s, symbol, e
            )
            i += 1
        start_states.setdefault(N, set()).add(State(init))
        final_states.setdefault(N, set()).add(State(i))

    boxes = set()
    for N in states.keys():
        box = Box(
            EpsilonNFA(
                states[N],
                symbols.setdefault(N, set()),
                transition_functions.setdefault(N, TransitionFunction()),
                start_states[N],
                final_states[N],
            ),
            Symbol(N.to_text()),
        )
        if N == cfg.start_symbol:
            start_symbol = Symbol(N.to_text())
        boxes.add(box)

    Ns = {Symbol(N.to_text()) for N in states.keys()}
    return RecursiveAutomaton(Ns, start_symbol, boxes)


def ebnf_to_rsm(ebnf: str) -> RecursiveAutomaton:
    productions = {}
    Ns = set()
    for production in ebnf.splitlines():
        production = production.strip()
        if "->" not in production:
            continue

        head, body = production.split("->")
        head = head.strip()
        body = body.strip()
        Ns.add(Symbol(head))

        if len(body) == 0:
            body = Epsilon().to_text()

        if head in productions:
            productions[head] += " | " + body
        else:
            productions[head] = body

    boxes = set()
    for head, body in productions.items():
        N = Symbol(head)
        boxes.add(Box(Regex(body).to_epsilon_nfa().minimize(), N))

    start_nonterminal = Symbol("S")
    return RecursiveAutomaton(Ns, start_nonterminal, boxes)


def rsm_to_mat(
    rsm: RecursiveAutomaton,
) -> tuple[dict[str, csr_matrix], int, set, set, set]:
    n = sum([len(box.dfa.states) for box in rsm.boxes.values()])

    rsm_state = set()
    rsm_start = set()
    rsm_final = set()
    for sym, box in rsm.boxes.items():
        rsm_state |= {(sym.value, state.value) for state in box.dfa.states}
        rsm_start |= {(sym.value, state.value) for state in box.dfa.start_states}
        rsm_final |= {(sym.value, state.value) for state in box.dfa.final_states}

    rsm_matrix = {}
    state_map = {state: i for i, state in enumerate(rsm_state)}
    for sym, box in rsm.boxes.items():
        for from_state, transitions in box.dfa.to_dict().items():
            for symbol, to_state in transitions.items():
                from_idx = state_map[(sym.value, from_state.value)]
                to_idx = state_map[(sym.value, to_state.value)]
                rsm_matrix.setdefault(symbol.value, csr_matrix((n, n), dtype=bool))[
                    from_idx, to_idx
                ] = True

    return rsm_matrix, n, rsm_state, rsm_start, rsm_final
