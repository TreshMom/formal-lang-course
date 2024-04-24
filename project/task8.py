import pyformlang
import scipy
from project import task3
from pyformlang.cfg import Epsilon
from scipy.sparse import dok_matrix
from networkx import DiGraph
from pyformlang.regular_expression import Regex
from project.task2 import graph_to_nfa
from pyformlang.rsa.box import Box
from pyformlang.rsa import RecursiveAutomaton
from pyformlang.finite_automaton import Symbol


def cfpq_with_tensor(
    rsm: pyformlang.rsa.RecursiveAutomaton,
    graph: DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    return "ok"
