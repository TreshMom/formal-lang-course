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
