from ast import Dict, Set, Tuple
from typing import Iterable
import networkx as nx
from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    NondeterministicFiniteAutomaton,
    Symbol,
)


class FiniteAutomaton:
    def __init__(self, states: Set[int], alphabet: Set[str], transitions: Dict[Tuple[int, str], Set[int]], 
                 start_states: Set[int], final_states: Set[int]):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_states = start_states
        self.final_states = final_states

    @classmethod
    def from_dfa(cls, dfa: DeterministicFiniteAutomaton):
        adjacency_matrix = nx.DiGraph()
        for state in dfa.states:
            adjacency_matrix.add_node(state)
        for state_from, transitions in dfa.to_dict().items():
            for symbol, state_to in transitions.items():
                adjacency_matrix.add_edge(state_from, state_to, label=symbol.value)
        start_states = dfa.start_states
        final_states = dfa.final_states
        return cls(adjacency_matrix, start_states, final_states)

    @classmethod
    def from_nfa(cls, nfa: NondeterministicFiniteAutomaton):
        adjacency_matrix = nx.DiGraph()
        for state in nfa.states:
            adjacency_matrix.add_node(state)
        for state_from, transitions in nfa.to_dict().items():
            for symbol, states_to in transitions.items():
                for state_to in states_to:
                    adjacency_matrix.add_edge(state_from, state_to, label=symbol.value)
        start_states = nfa.start_states
        final_states = nfa.final_states
        return cls(adjacency_matrix, start_states, final_states)

    def accepts(self, word: Iterable[Symbol]) -> bool:
        current_states = self.start_states
        for symbol in word:
            next_states = set()
            for state in current_states:
                next_states.update(
                    successor
                    for successor in self.adjacency_matrix.successors(state)
                    if self.adjacency_matrix[state][successor]["label"] == symbol.value
                )
            current_states = next_states
            if not current_states:
                return False
        return any(state in self.final_states for state in current_states)

    def is_empty(self) -> bool:
        visited = set()
        stack = list(self.start_states)
        while stack:
            state = stack.pop()
            if state in self.final_states:
                return False
            visited.add(state)
            stack.extend(
                successor
                for successor in self.adjacency_matrix.successors(state)
                if successor not in visited
            )
        return True

    def __str__(self):
        return "FiniteAutomaton(start={}, final={})".format(
            self.start_states, self.final_states
        )

def intersect_automata(automaton1: FiniteAutomaton, automaton2: FiniteAutomaton) -> FiniteAutomaton:
    adjacency_matrix = nx.DiGraph()
    for state1 in automaton1.adjacency_matrix.nodes:
        for state2 in automaton2.adjacency_matrix.nodes:
            adjacency_matrix.add_node((state1, state2))
    for (state1, state2) in adjacency_matrix.nodes:
        for symbol in automaton1.adjacency_matrix[state1]:
            if symbol in automaton2.adjacency_matrix[state2]:
                next_states1 = set(
                    successor
                    for successor in automaton1.adjacency_matrix[state1][symbol]
                )
                next_states2 = set(
                    successor
                    for successor in automaton2.adjacency_matrix[state2][symbol]
                )
                for next_state1 in next_states1:
                    for next_state2 in next_states2:
                        adjacency_matrix.add_edge(
                            (state1, state2), (next_state1, next_state2), label=symbol
                        )
    start_states = {(state1, state2) for state1 in automaton1.start_states for state2 in automaton2.start_states}
    final_states = {(state1, state2) for state1 in automaton1.final_states for state2 in automaton2.final_states}
    return FiniteAutomaton(adjacency_matrix, start_states, final_states)
