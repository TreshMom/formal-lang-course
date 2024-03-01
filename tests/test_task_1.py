import networkx as nx
import os
import tempfile
import pytest
from project import create_labeled_two_cycle_graph, graph_info


@pytest.fixture()
def start():
    print("Start test")


def test_create_labeled_two_cycle_graph():
    with tempfile.NamedTemporaryFile(suffix=".dot") as tmp_file:
        create_labeled_two_cycle_graph(3, 4, ("a", "b"), tmp_file.name)
        assert os.path.exists(tmp_file.name)

        G = nx.drawing.nx_pydot.read_dot(tmp_file.name)

        assert G.number_of_nodes() == 8
        assert G.number_of_edges() == 9
        for _, _, data in G.edges(data=True):
            assert data["label"] in ["a", "b"]


def test_graph_info():
    G = nx.Graph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2, {"label": "a"}), (2, 3, {"label": "b"})])

    node_count, edge_count, labels = graph_info(G)

    assert node_count == 3
    assert edge_count == 2
    assert labels == {"a", "b"}
