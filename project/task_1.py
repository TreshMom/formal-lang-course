import cfpq_data
from networkx.drawing import nx_pydot as pydot
from typing import Tuple, Set


def graph_info(name_graph: str) -> Tuple[int, int, Set[str]]:
    labels = set()
    for _, _, data in name_graph.edges(data=True):
        if "label" in data:
            labels.add(data["label"])

    return (name_graph.number_of_nodes(), name_graph.number_of_edges(), labels)


def create_labeled_two_cycle_graph(
    countNode1: int, countNode2: int, nameLabels: Tuple[str, str], path: str
) -> None:
    pydot.write_dot(
        G=cfpq_data.labeled_two_cycles_graph(
            n=countNode1,
            m=countNode2,
            labels=nameLabels,
        ),
        path=path,
    )
