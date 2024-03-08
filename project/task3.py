from networkx import MultiDiGraph
import scipy as sp
from typing import Iterable
from pyformlang.finite_automaton import *
from project.task2 import graph_to_nfa, regex_to_dfa


class FiniteAutomaton:
    def __init__(
        self,
        fa: NondeterministicFiniteAutomaton = None,
        *,
        matrix=None,
        start_states=None,
        final_states=None,
        state_to_int=None
    ) -> None:
        self.matrix = matrix
        self.start_states = start_states
        self.final_states = final_states
        self.state_to_int = state_to_int
        if fa is not None:
            self.state_to_int = {v: i for i, v in enumerate(fa.states)}
            self.matrix = to_matrix(fa, self.state_to_int)
            self.start_states = fa.start_states
            self.final_states = fa.final_states

    def accepts(self, word: Iterable[Symbol]) -> bool:
        return self.to_nfa().accepts(word)

    def is_empty(self) -> bool:
        return self.to_nfa().is_empty()

    def to_nfa(self) -> NondeterministicFiniteAutomaton:
        nfa = NondeterministicFiniteAutomaton()

        for symbol, matrix in self.matrix.items():
            for u, v in zip(*matrix.nonzero()):
                nfa.add_transition(
                    State(self.state_to_int[State(u)]),
                    symbol,
                    State(self.state_to_int[State(v)]),
                )

        for state in self.start_states:
            nfa.add_start_state(State(self.state_to_int[State(state)]))
        for state in self.final_states:
            nfa.add_final_state(State(self.state_to_int[State(state)]))

        return nfa


def to_matrix(
    fa: NondeterministicFiniteAutomaton, state_to_int=None
) -> dict[Symbol, sp.sparse.dok_matrix]:
    result = {}

    for symbol in fa.symbols:
        result[symbol] = sp.sparse.dok_matrix(
            (len(fa.states), len(fa.states)), dtype=bool
        )
        for v, edges in fa.to_dict().items():
            if symbol in edges:
                u = edges[symbol]
                result[symbol][state_to_int[v], state_to_int[u]] = True

    return result


def intersect_automata(
    atomaton1: FiniteAutomaton, atomaton2: FiniteAutomaton
) -> FiniteAutomaton:
    matrix = {}
    start_states = set()
    final_states = set()
    state_to_int = {}
    symbols = set(atomaton1.matrix.keys()) & set(atomaton2.matrix.keys())

    for symbol in symbols:
        matrix[symbol] = sp.sparse.kron(
            atomaton1.matrix[symbol], atomaton2.matrix[symbol], "csr"
        )

    for u in atomaton1.state_to_int:
        for v in atomaton2.state_to_int:
            k = (
                atomaton1.state_to_int[u] * len(atomaton2.state_to_int)
                + atomaton2.state_to_int[v]
            )
            state_to_int[k] = k

            if u in atomaton1.start_states and v in atomaton2.start_states:
                start_states.add(State(k))

            if u in atomaton1.final_states and v in atomaton2.final_states:
                final_states.add(State(k))

    return FiniteAutomaton(
        matrix=matrix,
        start_states=start_states,
        final_states=final_states,
        state_to_int=state_to_int,
    )


def paths_ends(
    graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int], regex: str
) -> list:
    nfa = graph_to_nfa(graph)
    dfa = regex_to_dfa(regex)
    automaton = intersect_automata(nfa, dfa)
    automaton_paths = automaton.to_nfa().get_paths(start_nodes, final_nodes)
    return automaton_paths
