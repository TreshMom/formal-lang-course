from pyformlang.cfg import CFG


def cfg_to_wnf(cfg: CFG) -> CFG:
    return CFG(
        start_symbol=cfg.start_symbol,
        productions=cfg.eliminate_unit_productions()
        .remove_useless_symbols()
        ._decompose_productions(cfg._get_productions_with_only_single_terminals()),
    )


def cfg_from_file(path: str) -> CFG:
    with open(path) as f:
        return CFG.from_text(f.read())
