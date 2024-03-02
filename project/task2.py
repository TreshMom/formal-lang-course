from pyformlang.regular_expression import *
from pyformlang.finite_automaton import *
from networkx import MultiDiGraph
from typing import Set


def regex_to_dfa(regex: str) -> DeterministicFiniteAutomaton:
    return Regex(regex).to_epsilon_nfa().minimize()


def graph_to_nfa(
    graph: MultiDiGraph, start_states: Set[int], final_states: Set[int]
) -> NondeterministicFiniteAutomaton:
    nfa = NondeterministicFiniteAutomaton()

    states = set(graph.nodes())

    final_states = final_states if final_states else states
    start_states = start_states if start_states else states

    for final_state in final_states:
        nfa.add_final_state(State(final_state))

    for start_state in start_states:
        nfa.add_start_state(State(start_state))

    for f, t, l in graph.edges(data="label"):
        nfa.add_transition(State(f), l, State(t))

    return nfa
