import scipy
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
    m = None
    start = None
    final = None
    mapping = None

    def __init__(self, automata, start=None, final=None, mapping=None):
        if mapping is None:
            mapping = dict()
        if final is None:
            final = set()
        if start is None:
            start = set()

        # TODO make this check also in types
        if isinstance(automata, DeterministicFiniteAutomaton) or isinstance(
            automata, NondeterministicFiniteAutomaton
        ):
            mat = nfa_to_matrix(automata)
            self.m, self.start, self.final, self.mapping = (
                mat.m,
                mat.start,
                mat.final,
                mat.mapping,
            )
        else:
            self.m, self.start, self.final, self.mapping = (
                automata,
                start,
                final,
                mapping,
            )

    def accepts(self, word) -> bool:
        nfa = matrix_to_nfa(self)
        return nfa.accepts("".join(list(word)))

    def is_empty(self) -> bool:
        return len(self.m.values()) == 0

    def mapping_for(self, u) -> State:
        return self.mapping[State(u)]

    def size(self):
        return len(self.mapping)

    def starts(self):
        return [self.mapping_for(t) for t in self.start]

    def ends(self):
        return [self.mapping_for(t) for t in self.final]

    def labels(self):
        return self.mapping.keys()


def nfa_to_matrix(automaton: NondeterministicFiniteAutomaton) -> FiniteAutomaton:
    states = automaton.to_dict()
    len_states = len(automaton.states)
    mapping = {v: i for i, v in enumerate(automaton.states)}
    m = dict()

    def as_set(obj):
        if not isinstance(obj, set):
            return {obj}
        return obj

    for label in automaton.symbols:
        m[label] = dok_matrix((len_states, len_states), dtype=bool)
        for u, edges in states.items():
            if label in edges:
                for v in as_set(edges[label]):
                    m[label][mapping[u], mapping[v]] = True

    return FiniteAutomaton(m, automaton.start_states, automaton.final_states, mapping)


def matrix_to_nfa(automaton: FiniteAutomaton) -> NondeterministicFiniteAutomaton:
    nfa = NondeterministicFiniteAutomaton()

    for label in automaton.m.keys():
        m_size = automaton.m[label].shape[0]
        for u in range(m_size):
            for v in range(m_size):
                if automaton.m[label][u, v]:
                    nfa.add_transition(
                        automaton.mapping_for(u), label, automaton.mapping_for(v)
                    )

    for s in automaton.start:
        nfa.add_start_state(automaton.mapping_for(s))
    for s in automaton.final:
        nfa.add_final_state(automaton.mapping_for(s))

    return nfa


def intersect_automata(
    automaton1: FiniteAutomaton, automaton2: FiniteAutomaton, take_from_mapping=False
) -> FiniteAutomaton:
    labels = None
    if take_from_mapping:
        labels = automaton1.mapping.keys() & automaton2.mapping.keys()
    else:
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

            assert isinstance(u, State)
            if u in automaton1.start and v in automaton2.start:
                start.add(State(k))

            if u in automaton1.final and v in automaton2.final:
                final.add(State(k))

    return FiniteAutomaton(m, start, final, mapping)


def paths_ends(
    graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int], regex: str
) -> list[tuple[NodeView, NodeView]]:
    automaton_regex = nfa_to_matrix(regex_to_dfa(regex))
    automaton_graph = nfa_to_matrix(graph_to_nfa(graph, start_nodes, final_nodes))
    intersection = intersect_automata(automaton_graph, automaton_regex, True)
    fa_closure = make_transitive_closure(intersection)

    size = automaton_regex.size()
    result = list()
    for u, v in zip(*fa_closure.nonzero()):
        if u in intersection.start and v in intersection.final:
            result.append(
                (automaton_graph.mapping[u // size], automaton_graph.mapping[v // size])
            )

    return result


def make_transitive_closure(fa: FiniteAutomaton):
    if fa.is_empty():
        return dok_matrix((0, 0), dtype=bool)

    f = None
    for m in fa.m.values():
        f = m if f is None else f + m

    p = 0
    while f.count_nonzero() != p:
        p = f.count_nonzero()
        f += f @ f

    return f
