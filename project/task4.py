from typing import Dict, Set
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order
from .task3 import FiniteAutomaton

def reachability_with_constraints(fa: FiniteAutomaton,
                                  constraints_fa: FiniteAutomaton) -> Dict[int, Set[int]]:
    num_states = fa.num_states()
    adjacency_matrix = np.zeros((num_states, num_states), dtype=int)
    for transition in fa.transitions:
        adjacency_matrix[transition[0], transition[2]] = 1
    graph = csr_matrix(adjacency_matrix)
    start_states = fa.initial_states
    reachable_from_starts = {}
    for start_state in start_states:
        _, predecessors = breadth_first_order(graph, start_state, return_predecessors=True)
        reachable_states = set()
        for state in range(num_states):
            if predecessors[state] != -9999 and constraints_fa.accepts(state):
                reachable_states.add(state)
        reachable_from_starts[start_state] = reachable_states

    return reachable_from_starts
