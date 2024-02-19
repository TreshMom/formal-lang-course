import cfpq_data
from networkx.drawing import nx_pydot as pydot
from typing import Tuple
from typing import Any, Tuple, Set
from cfpq_data import *

path = download("generations")
bzip = cfpq_data.graph_from_csv(path)

def get_graph_info(graph: Any) -> Tuple[int, int, Set[str]]:
    countNode = graph.number_of_nodes()
    countEdges = graph.number_of_edges()
    countLabels = set()
    for edge in graph.edges:
        countLabels.add(edge.attr['label'])


    return countNode, countEdges, countLabels

def save_labeled_two_cycle_graph(
        countNode1: int, countNode2: int, nameLabels: Tuple[str,str], path: str 
        ) -> None:
    pydot.write_dot(
    G = cfpq_data.labeled_two_cycles_graph(
        n=countNode1,
        m=countNode2,
        labels=nameLabels,
    ),
    path=path,
    )
