import scipy
from itertools import product
from networkx import MultiDiGraph
from networkx.classes.reportviews import NodeView
from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    NondeterministicFiniteAutomaton,
    State,
)
from scipy.sparse import dok_matrix, kron

from project.task2 import regex_to_dfa, graph_to_nfa


class FiniteAutomaton:
    matrix = None
    start_states = None
    final_states = None
    states_count: int = None

    # TODO: type for finite_automaton
    def __init__(self, finite_automaton=None):
        if finite_automaton is None:
            return

        state_to_i = {s: i for i, s in enumerate(finite_automaton.states)}

        self.states_list = list(finite_automaton.states)

        self.start_states = {state_to_i[st] for st in finite_automaton.start_states}
        self.final_states = {state_to_i[fi] for fi in finite_automaton.final_states}

        self.matrix = {}

        states = finite_automaton.to_dict()
        n = len(finite_automaton.states)

        for l in finite_automaton.symbols:
            self.matrix[l] = dok_matrix((n, n), dtype=bool)
            for st, ls in states.items():
                if l in ls:
                    for fi in ls[l] if isinstance(ls[l], set) else {ls[l]}:
                        self.matrix[l][state_to_i[st], state_to_i[fi]] = True

    def accepts(self, word) -> bool:
        nfa = matrix_to_nfa(self)
        return nfa.accepts("".join(list(word)))

    def is_empty(self) -> bool:
        if len(self.matrix) == 0:
            return True
        m = sum(self.matrix.values())
        for _ in range(m.shape[0]):
            m += m @ m
        for st, fi in product(self.start_states, self.final_states):
            if m[st, fi] != 0:
                return False
        return True

    def size(self):
        return len(self.states_list)

    def starts(self):
        return self.start_states

    def ends(self):
        return self.final_states

    def labels(self):
        return self.matrix.keys()


def matrix_to_nfa(automaton: FiniteAutomaton) -> NondeterministicFiniteAutomaton:
    nfa = NondeterministicFiniteAutomaton()

    for l, m in automaton.matrix.items():
        nfa.add_transitions(
            [
                (st, l, fi)
                for (st, fi) in product(range(m.shape[0]), repeat=2)
                if automaton.matrix[l][st, fi]
            ]
        )

    for s in automaton.start_states:
        nfa.add_start_state(s)
    for s in automaton.final_states:
        nfa.add_final_state(s)

    return nfa


def intersect_automata(
    automaton1: FiniteAutomaton, automaton2: FiniteAutomaton
) -> FiniteAutomaton:

    ls = automaton1.matrix.keys() & automaton2.matrix.keys()
    fa = FiniteAutomaton()
    fa.matrix = {}

    for l in ls:
        fa.matrix[l] = kron(automaton1.matrix[l], automaton2.matrix[l], "csr")

    fa.start_states = set()
    fa.final_states = set()

    n_states2 = automaton2.matrix.values().__iter__().__next__().shape[0]

    for i, j in product(automaton1.start_states, automaton2.start_states):
        fa.start_states.add(i * (n_states2) + j)
    for i, j in product(automaton1.final_states, automaton2.final_states):
        fa.final_states.add(i * (n_states2) + j)

    return fa


def paths_ends(
    graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int], regex: str
) -> list[tuple[int, int]]:
    fa1 = FiniteAutomaton(graph_to_nfa(graph, start_nodes, final_nodes))
    fa2 = FiniteAutomaton(regex_to_dfa(regex))
    fa = intersect_automata(fa1, fa2)

    n_states2 = fa2.matrix.values().__iter__().__next__().shape[0]

    def extract_fa1_node_idx(i):
        return fa1.states_list[i // n_states2].value

    res = set()
    for st in fa.start_states & fa.final_states:
        n = extract_fa1_node_idx(st)
        res.add((n, n))

    if len(fa.matrix) == 0:
        return res

    m = sum(fa.matrix.values())
    for _ in range(m.shape[0]):
        m += m @ m

    for st, fi in product(fa.start_states, fa.final_states):
        if m[st, fi] != 0:
            res.add((extract_fa1_node_idx(st), extract_fa1_node_idx(fi)))

    return list(res)
