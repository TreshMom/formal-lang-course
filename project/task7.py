import networkx as nx
import scipy.sparse
from pyformlang.cfg import CFG, Variable, Epsilon


def cfg_to_weak_normal_form(cfg: CFG) -> CFG:
    clear_cfg = cfg.eliminate_unit_productions().remove_useless_symbols()
    decomposed = clear_cfg._decompose_productions(
        clear_cfg._get_productions_with_only_single_terminals()
    )
    return CFG(productions=set(decomposed), start_symbol=Variable("S"))


def cfpq_with_matrix(
    cfg: CFG,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:

    cfg_weak = cfg_to_weak_normal_form(cfg)
    nodes_len = len(graph.nodes)
    pre_res = {
        v: scipy.sparse.dok_matrix((nodes_len, nodes_len), dtype=bool)
        for v in cfg_weak.variables
    }
    ni_to_nj_nk = set()

    for i, j, tag in graph.edges.data("label"):
        for prod in cfg_weak.productions:
            if (
                len(prod.body) == 1
                and isinstance(prod.body[0], Variable)
                and prod.body[0].value == tag
            ):
                pre_res[prod.head][i, j] = True
            elif len(prod.body) == 1 and isinstance(prod.body[0], Epsilon):
                pre_res[prod.head] += scipy.sparse.csr_matrix(
                    scipy.sparse.eye(nodes_len), dtype=bool
                )
            elif len(prod.body) == 2:
                ni_to_nj_nk.add((prod.head, prod.body[0], prod.body[1]))

    res_csrs = {x: scipy.sparse.csr_matrix(matrix) for x, matrix in pre_res.items()}

    not_changed = False
    while not not_changed:
        not_changed = True
        for ni, nj, nk in ni_to_nj_nk:
            prev = res_csrs[ni].nnz
            res_csrs[ni] += res_csrs[nj] @ res_csrs[nk]
            if prev != res_csrs[ni].nnz:
                not_changed = False

    result = {
        (i, j) for k, matrix in res_csrs.items() for i, j in zip(*matrix.nonzero())
    }

    return result
