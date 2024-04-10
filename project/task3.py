from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    NondeterministicFiniteAutomaton,
    State,
)
from scipy.sparse import dok_matrix, kron
from networkx import MultiDiGraph
from project.task2 import graph_to_nfa, regex_to_dfa


def as_set(obj):
    if not isinstance(obj, set):
        return {obj}
    return obj


class FiniteAutomaton:
    m = None
    start = None
    final = None
    mapping = None

    def __init__(self, obj, start=set(), final=set(), mapping=dict()):
        if isinstance(
            obj, (DeterministicFiniteAutomaton, NondeterministicFiniteAutomaton)
        ):
            matrix = nfa_to_matrix(obj)
            self.m = matrix.m
            self.start = matrix.start
            self.final = matrix.final
            self.mapping = matrix.mapping
        else:
            self.m = obj
            self.start = start
            self.final = final
            self.mapping = mapping

    def map_for(self, u):
        return self.mapping[State(u)]

    def size(self):
        return len(self.mapping)

    def start_idx(self):
        return [self.map_for(i) for i in self.start]

    def final_idx(self):
        return [self.map_for(i) for i in self.final]

    def labels(self):
        return self.m.keys()

    def accepts(self, word):
        nfa = matrix_to_nfa(self)
        real_word = "".join(list(word))
        return nfa.accepts(real_word)

    def is_empty(self):
        return len(self.m) == 0 or len(next(self.m.values())) == 0


def nfa_to_matrix(automaton: NondeterministicFiniteAutomaton) -> FiniteAutomaton:
    states = automaton.to_dict()
    states_num = len(automaton.states)
    mapping = {v: i for i, v in enumerate(automaton.states)}
    m = dict()
    for label in automaton.symbols:
        m[label] = dok_matrix((states_num, states_num), dtype=bool)
        for u, edges in states.items():
            if label in edges:
                for v in as_set(edges[label]):
                    m[label][mapping[u], mapping[v]] = True
    return FiniteAutomaton(m, automaton.start_states, automaton.final_states, mapping)


def matrix_to_nfa(automaton: FiniteAutomaton) -> NondeterministicFiniteAutomaton:
    nfa = NondeterministicFiniteAutomaton()
    for label in automaton.m.keys():
        size = automaton.m[label].shape[0]
        for u in range(size):
            for v in range(size):
                if automaton.m[label][u, v]:
                    nfa.add_transition(
                        automaton.map_for(u), label, automaton.map_for(v)
                    )
    for s in automaton.start:
        nfa.add_start_state(automaton.map_for(s))
    for s in automaton.final:
        nfa.add_final_state(automaton.map_for(s))
    return nfa


def transitive_closure(automaton: FiniteAutomaton):
    if len(automaton.m.values()) == 0:
        return dok_matrix((0, 0), dtype=bool)
    adj = sum(automaton.m.values())
    for i in range(adj.shape[0]):
        adj += adj @ adj
    return adj


def intersect_automata(
    automaton1: FiniteAutomaton, automaton2: FiniteAutomaton
) -> FiniteAutomaton:
    labels = automaton1.m.keys() & automaton2.m.keys()
    m = dict()
    start = set()
    final = set()
    mapping = dict()
    for label in labels:
        m[label] = kron(automaton1.m[label], automaton2.m[label], "csr")
    for u, i in automaton1.mapping.items():
        for v, j in automaton2.mapping.items():
            k = len(automaton2.mapping) * i + j
            mapping[k] = k
            if u in automaton1.start and v in automaton2.start:
                start.add(State(k))
            if u in automaton1.final and v in automaton2.final:
                final.add(State(k))
    return FiniteAutomaton(m, start, final, mapping)


def paths_ends(
    graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int], regex: str
) -> list[tuple[object, object]]:
    nfa = nfa_to_matrix(graph_to_nfa(graph, start_nodes, final_nodes))
    dfa = nfa_to_matrix(regex_to_dfa(regex))
    intersec = intersect_automata(nfa, dfa)
    clos = transitive_closure(intersec)
    mapping = {v: i for i, v in nfa.mapping.items()}
    size = len(dfa.mapping)
    res = list()
    for u, v in zip(*clos.nonzero()):
        if u in intersec.start and v in intersec.final:
            res.append((mapping[u // size], mapping[v // size]))
    return res
