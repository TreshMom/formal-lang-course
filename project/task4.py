import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order
from project.task3 import FiniteAutomaton


def reachability_with_constraints(
    fa: FiniteAutomaton, constraints_fa: FiniteAutomaton
) -> dict[int, set[int]]:
    # Построение разреженной матрицы для графа автомата
    num_states = fa.num_states
    transitions = fa.transitions
    adjacency_matrix = np.zeros((num_states, num_states), dtype=bool)
    for state, next_state in transitions:
        adjacency_matrix[state, next_state] = True

    # Преобразование разреженной матрицы в формат CSR для эффективного доступа к строкам
    csr_adjacency_matrix = csr_matrix(adjacency_matrix)

    # Словарь для хранения достижимых вершин из каждой стартовой вершины
    reachable_states = {}

    # Обработка каждой из стартовых вершин
    for start_state in range(num_states):
        # Используем алгоритм multiple source BFS для нахождения достижимых вершин из текущей стартовой вершины
        _, predecessors = breadth_first_order(
            csr_adjacency_matrix, i_start=start_state, return_predecessors=True
        )

        # Стартовая вершина также является достижимой из себя
        reachable_set = set([start_state])

        # Добавляем предшествующие вершины в множество достижимых вершин
        for pred_state, _ in enumerate(predecessors):
            if (
                pred_state != start_state and predecessors[pred_state] != -9999
            ):  # -9999 обозначает отсутствие пути
                reachable_set.add(pred_state)

        # Добавляем найденное множество достижимых вершин в словарь
        reachable_states[start_state] = reachable_set

    return reachable_states
