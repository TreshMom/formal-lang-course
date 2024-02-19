import cfpq_data
import networkx as nx
import random
import matplotlib.pyplot as plt

n = 3  # количество вершин
p = 0.3  # вероятность соединения вершин

random_graph = nx.erdos_renyi_graph(n, p)
print(random_graph.nodes())
print(random_graph.edges())
print(random_graph.number_of_nodes())
'''
fig, ax = plt.subplots()  # создать фигуру и оси
nx.draw(random_graph, with_labels=True, ax=ax)  # сделать рисунок на указанных осях
plt.show()  # показать граф
'''