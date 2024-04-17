import itertools
import pyformlang
import networkx as nx
import scipy

from project.task6 import cfg_to_weak_normal_form
from collections import defaultdict
from typing import Generic
from typing import Iterable
from typing import Iterator
from typing import Tuple
from typing import TypeVar
from collections import deque
from typing import Dict
from typing import List
from typing import Set

T = TypeVar("T")


class BoolDecomposition(Generic[T]):
    def __init__(
        self, shape: Tuple[int, int], content: Iterable[Tuple[int, int, T]] = None
    ):
        self.matrices = defaultdict(lambda: scipy.sparse.csr_matrix(shape))
        self.shape = shape
        dok_matrices = dict()
        if content:
            for i, j, element in content:
                if element not in dok_matrices:
                    dok_matrices[element] = scipy.sparse.dok_matrix(
                        self.shape, dtype=bool
                    )
                dok_matrices[element][i, j] = True
            for element, matrix in dok_matrices.items():
                self.matrices[element] = matrix.tocsr()

    def __iter__(self) -> Iterator[Tuple[int, int, T]]:
        return (
            (i, j, element)
            for (element, matrix) in self.matrices.items()
            for (i, j) in (zip(*matrix.nonzero()))
        )

    def __getitem__(self, element: T) -> scipy.sparse.csr_matrix:
        return self.matrices[element]

    def __setitem__(self, element: T, matrix: scipy.sparse.csr_matrix):
        self.matrices[element] = matrix

    def count_nonzero(self) -> int:
        return sum(matrix.count_nonzero() for matrix in self.matrices.values())

    def kron(self, other: "BoolDecomposition[T]") -> "BoolDecomposition[T]":
        result = BoolDecomposition(
            (self.shape[0] * other.shape[0], self.shape[1] * other.shape[1])
        )
        for element, matrix in self.matrices.items():
            if element in other.matrices:
                result.matrices[element] = scipy.sparse.kron(
                    matrix, other.matrices[element], format="csr"
                )
        return result

    def transitive_closure(self) -> scipy.sparse.csr_matrix:
        if self.shape[0] != self.shape[1]:
            raise Exception(
                "Unable to get transitive closure for non square boolean decomposition"
            )
        result: scipy.sparse.csr_matrix = sum(
            self.matrices.values(),
            start=scipy.sparse.identity(self.shape[0], dtype=bool, format="csr"),
        )
        prev_non_zeros = 0
        non_zeros = result.count_nonzero()
        while prev_non_zeros != non_zeros:
            result += result @ result
            prev_non_zeros = non_zeros
            non_zeros = result.count_nonzero()
        return result


def _filter_cfpq_result(
    cfpq_result: Set[Tuple[int, pyformlang.cfg.Variable, int]],
    cfg: pyformlang.cfg.CFG,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> Set[Tuple[int, int]]:
    return {
        (start, finish)
        for (start, var, finish) in cfpq_result
        if var == cfg.start_symbol
        and (start_nodes is None or start in start_nodes)
        and (final_nodes is None or finish in final_nodes)
    }


def _cfpq_with_matrix(
    cfg: pyformlang.cfg.CFG, graph: nx.DiGraph
) -> Set[Tuple[int, pyformlang.cfg.Variable, int]]:
    cfg = cfg_to_weak_normal_form(cfg)
    terminal_to_generating_vars: Dict[str, List[pyformlang.cfg.Variable]] = defaultdict(
        list
    )
    vars_generating_epsilon: List[pyformlang.cfg.Variable] = []
    variable_productions: List[
        Tuple[pyformlang.cfg.Variable, pyformlang.cfg.Variable, pyformlang.cfg.Variable]
    ] = []
    for production in cfg.productions:
        match production.body:
            case [] | [pyformlang.cfg.Epsilon()]:
                vars_generating_epsilon.append(production.head)
            case [pyformlang.cfg.Terminal() as terminal]:
                terminal_to_generating_vars[terminal.value].append(production.head)
            case [pyformlang.cfg.Variable() as var1, pyformlang.cfg.Variable() as var2]:
                variable_productions.append((production.head, var1, var2))
    node_to_idx = {node: idx for (idx, node) in enumerate(graph.nodes)}
    idx_to_node = {idx: node for (idx, node) in enumerate(graph.nodes)}
    is_reachable = BoolDecomposition(
        (graph.number_of_nodes(), graph.number_of_nodes()),
        content=itertools.chain(
            (
                (node_to_idx[start], node_to_idx[finish], var)
                for (start, finish, attributes) in graph.edges.data()
                for var in terminal_to_generating_vars[attributes["label"]]
            ),
            (
                (node_idx, node_idx, var)
                for node_idx in range(graph.number_of_nodes())
                for var in vars_generating_epsilon
            ),
        ),
    )
    prev_non_zeros = 0
    non_zeros = is_reachable.count_nonzero()
    while prev_non_zeros != non_zeros:
        for head, var1, var2 in variable_productions:
            is_reachable[head] += is_reachable[var1] @ is_reachable[var2]
        prev_non_zeros = non_zeros
        non_zeros = is_reachable.count_nonzero()
    return {
        (idx_to_node[start_idx], var, idx_to_node[finish_idx])
        for (start_idx, finish_idx, var) in is_reachable
    }


def cfpq_with_matrix(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> Set[Tuple[int, int]]:
    return _filter_cfpq_result(
        _cfpq_with_matrix(cfg, graph), cfg, start_nodes, final_nodes
    )
