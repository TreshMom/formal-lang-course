import cfpq_data
from networkx.drawing import nx_pydot as pydot
from typing import Tuple, Set


def graph_info(name_graph: str) -> Tuple[int, int, Set[str]]:
    graph_path = cfpq_data.download(name_graph)
    graph = cfpq_data.graph_from_csv(graph_path)
    labels = set()
    for _, _, data in graph.edges(data=True):
        if 'label' in data:
            labels.add(data['label'])


    return (
        graph.number_of_nodes(),
        graph.number_of_edges(),
        labels
    )


def create_labeled_two_cycle_graph(
        countNode1: int, countNode2: int, nameLabels: Tuple[str, str],
        path: str) -> None:
    pydot.write_dot(
        G=cfpq_data.labeled_two_cycles_graph(
            n=countNode1,
            m=countNode2,
            labels=nameLabels,
        ),
        path=path,
    )
#create_labeled_two_cycle_graph(3,4,("a","b"),'1')
path = 'bzip'
print(graph_info(path))