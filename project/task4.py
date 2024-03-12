import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order
from project.task3 import FiniteAutomaton


def reachability_with_constraints(
    fa: FiniteAutomaton, constraints_fa: FiniteAutomaton
) -> dict[int, set[int]]:
    num_states = fa.num_states
    transitions = fa.transitions
    adjacency_matrix = np.zeros((num_states, num_states), dtype=bool)
    for state, next_state in transitions:
        adjacency_matrix[state, next_state] = True

    csr_adjacency_matrix = csr_matrix(adjacency_matrix)

    reachable_states = {}

    for start_state in range(num_states):
        _, predecessors = breadth_first_order(
            csr_adjacency_matrix, i_start=start_state, return_predecessors=True
        )

        reachable_set = set([start_state])

        for pred_state, _ in enumerate(predecessors):
            if pred_state != start_state and predecessors[pred_state] != -9999:
                reachable_set.add(pred_state)
        reachable_states[start_state] = reachable_set

    return reachable_states
