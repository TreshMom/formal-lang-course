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

    if not start_states:
        start_states = set(graph.nodes())
    if not final_states:
        final_states = set(graph.nodes())

    for state in start_states:
        nfa.add_start_state(State(state))
    for state in final_states:
        nfa.add_final_state(State(state))
    for s, e, label in graph.edges(data="label"):
        nfa.add_transition(s, label, e)

    return nfa
