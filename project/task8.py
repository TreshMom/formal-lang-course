import pyformlang
import scipy
from project import automaton
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

    mat = automaton.rsm_to_mat(rsm)
    graph_mat = automaton.nfa_to_mat(graph_to_nfa(graph, start_nodes, final_nodes))
    mat_inds = mat.indexes_dict()
    graph_mat_inds = graph_mat.indexes_dict()

    n = graph_mat.states_count

    for var in mat.nullable_symbols:
        if var not in graph_mat.m:
            graph_mat.m[var] = dok_matrix((n, n), dtype=bool)
        graph_mat.m[var] += scipy.sparse.eye(n, dtype=bool)

    last_nnz = 0
    while True:

        closure = automaton.transitive_closure(
            automaton.intersect_automata(mat, graph_mat)
        ).nonzero()
        closure = list(zip(*closure))

        curr_nnz = len(closure)
        if curr_nnz == last_nnz:
            break
        last_nnz = curr_nnz

        for i, j in closure:
            src = mat_inds[i // n]
            dst = mat_inds[j // n]

            if src in mat.start and dst in mat.final:
                var = src.value[0]
                if var not in graph_mat.m:
                    graph_mat.m[var] = dok_matrix((n, n), dtype=bool)
                graph_mat.m[var][i % n, j % n] = True

    return {
        (graph_mat_inds[i], graph_mat_inds[j])
        for _, m in graph_mat.m.items()
        for i, j in zip(*m.nonzero())
        if graph_mat_inds[i] in mat.start and graph_mat_inds[j] in mat.final
    }


def cfg_to_rsm(cfg: pyformlang.cfg.CFG) -> pyformlang.rsa.RecursiveAutomaton:
    prods = {}
    for p in cfg.productions:
        if len(p.body) == 0:
            regex = Regex(
                " ".join(
                    "$" if isinstance(var, Epsilon) else var.value for var in p.body
                )
            )
        else:
            regex = Regex("$")
        if Symbol(p.head) not in prods:
            prods[Symbol(p.head)] = regex
        else:
            prods[Symbol(p.head)] = prods[Symbol(p.head)].union(regex)

    prods = {
        Symbol(var): Box(regex.to_epsilon_nfa().to_deterministic(), Symbol(var))
        for var, regex in prods.items()
    }

    return pyformlang.rsa.RecursiveAutomaton(
        set(prods.keys()), Symbol("S"), set(prods.values())
    )


def ebnf_to_rsm(ebnf: str) -> pyformlang.rsa.RecursiveAutomaton:
    prods = {}
    boxes = set()
    for p in ebnf.splitlines():
        p = p.strip()
        if "->" not in p:
            continue

        head, body = p.split("->")
        head = head.strip()
        body = body.strip() if body.strip() != "" else Epsilon().to_text()

        if head in prods:
            prods[head] += " | " + body
        else:
            prods[head] = body

    prods = {
        Symbol(var): Box(Regex(regex).to_epsilon_nfa().to_deterministic(), Symbol(var))
        for var, regex in prods.items()
    }

    return RecursiveAutomaton(set(prods.keys()), Symbol("S"), set(prods.values()))
