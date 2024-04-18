from scipy.sparse import dok_matrix, block_diag

from project.task3 import (
    FiniteAutomaton,
)


def reachability_with_constraints(
    fa: FiniteAutomaton, constraints_fa: FiniteAutomaton
) -> dict[int, set[int]]:

    m, n = constraints_fa.size(), fa.size()

    def get_front(s):
        front = dok_matrix((m, m + n), dtype=bool)
        for i in constraints_fa.starts():
            front[i, i] = True
        for i in range(m):
            front[i, s + m] = True
        return front

    def diagonalized(mat):
        result = dok_matrix(mat.shape, dtype=bool)
        for i in range(mat.shape[0]):
            for j in range(mat.shape[0]):
                if mat[j, i]:
                    result[i] += mat[j]
        return result

    labels = fa.labels() & constraints_fa.labels()
    result = {s: set() for s in fa.start}
    adj = {
        label: block_diag((constraints_fa.m[label], fa.m[label]), "csr")
        for label in labels
    }

    for v in fa.starts():
        front = get_front(v)
        last_nnz = -1
        for _ in range(m * n):
            front = sum(
                [dok_matrix((m, m + n), dtype=bool)]
                + [diagonalized(front @ adj[label]) for label in labels]
            )
            k = front[:, m:].nonzero()
            for x, y in zip(k[0], k[1]):
                if x in constraints_fa.ends() and y in fa.ends():
                    result[v].add(y)
            if hash(str(k)) == last_nnz:
                break
            last_nnz = hash(str(k))

    return result
from project.task3 import FiniteAutomaton
from scipy.sparse import dok_matrix, block_diag


def reachability_with_constraints(
    finite_automaton: FiniteAutomaton,
    constraints_automaton: FiniteAutomaton,
    start_to_end_enable: bool = True,
) -> dict[int, set[int]]:
    matrices = {}

    common_labels = (
        finite_automaton.func_to_steps.keys()
        & constraints_automaton.func_to_steps.keys()
    )
    constraints_height, automaton_height = len(
        constraints_automaton.map_index_to_state
    ), len(finite_automaton.map_index_to_state)

    for label in common_labels:
        constraints_matrix = constraints_automaton.func_to_steps[label]
        automaton_matrix = finite_automaton.func_to_steps[label]
        matrices[label] = block_diag((constraints_matrix, automaton_matrix))

    height = constraints_height
    width = constraints_height + automaton_height

    reachable_states = {
        state.value: set() for state in finite_automaton.map_index_to_state
    }

    def diagonalize_matrix(matrix):
        height = matrix.shape[0]
        result = dok_matrix(matrix.shape, dtype=bool)

        for i in range(height):
            for j in range(height):
                if matrix[j, i]:
                    result[i] += matrix[j]

        return result

    for start_state in finite_automaton.start_states:
        frontier = dok_matrix((height, width), dtype=bool)
        for constraints_start_state in constraints_automaton.start_states:
            frontier[constraints_start_state, constraints_start_state] = True

        for i in range(height):
            frontier[i, start_state + constraints_height] = True

        for _ in range(constraints_height * automaton_height):
            new_frontier = dok_matrix((height, width), dtype=bool)
            for label in common_labels:
                new_frontier += diagonalize_matrix(frontier @ matrices[label])
            frontier = new_frontier
            for i in range(height):
                if i in constraints_automaton.final_states and frontier[i, i]:
                    for j in range(automaton_height):
                        if (
                            j in finite_automaton.final_states
                            and frontier[i, j + constraints_height]
                        ):
                            if (
                                start_to_end_enable
                                or finite_automaton.map_index_to_state[start_state]
                                != finite_automaton.map_index_to_state[j]
                            ):
                                reachable_states[
                                    finite_automaton.map_index_to_state[start_state]
                                ].add(finite_automaton.map_index_to_state[j])

    return reachable_states
