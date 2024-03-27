from pyformlang.cfg import CFG


def cfg_to_wnf(cfg: CFG) -> CFG:
    cfg1 = cfg.eliminate_unit_productions().remove_useless_symbols()
    tmp = cfg1._get_productions_with_only_single_terminals()
    new_rules = set(cfg1._decompose_productions(tmp))
    return CFG(start_symbol=cfg1.start_symbol, productions=new_rules)


def cfg_from_file(path: str) -> CFG:
    with open(path) as f:
        return CFG.from_text(f.read())
