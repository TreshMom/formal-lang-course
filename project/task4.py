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
    result = {s.value: set() for s in fa.states_list}
    adj = {
        label: block_diag((constraints_fa.matrix[label], fa.matrix[label]))
        for label in labels
    }

    for state in fa.starts():
        front = get_front(state)
        if state in fa.final_states:
            for i in constraints_fa.start_states:
                if i in constraints_fa.final_states:
                    result[fa.states_list[state]].add(fa.states_list[state])

        for _ in range(m * n):
            new_front = dok_matrix((m, m + n), dtype=bool)
            for l in labels:
                new_front += diagonalized(front @ adj[l])
            front = new_front
            for i in range(m):
                if i in constraints_fa.final_states and front[i, i]:
                    for j in range(n):
                        if j in fa.final_states and front[i, j + m]:
                            result[fa.states_list[state]].add(fa.states_list[j])

    return result
