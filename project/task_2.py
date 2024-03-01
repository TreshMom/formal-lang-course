from pyformlang.regular_expression import *
from pyformlang.finite_automaton import *
from networkx import MultiDiGraph
from typing import Set


def regex_to_min_dfa(regex: str) -> DeterministicFiniteAutomaton:
    return Regex(regex).to_epsilon_nfa().minimize()


def create_nfa(
    graph: MultiDiGraph, 
    start_states: Set[int] = None,
    final_states: Set[int] = None
) -> NondeterministicFiniteAutomaton:
    
    nfa = NondeterministicFiniteAutomaton()

    for edge in graph.edges(data=True):
        nfa.add_transition(State(edge[0]), Symbol(edge[2]["label"]), State(edge[1]))

    if start_states is None and final_states is None:
        for state in nfa.states:
            nfa.add_start_state(state)
            nfa.add_final_state(state)

    if start_states is not None:
        for state in start_states:
            nfa.add_start_state(State(state))

    if final_states is not None:
        for state in final_states:
            nfa.add_final_state(State(state))

    return nfa