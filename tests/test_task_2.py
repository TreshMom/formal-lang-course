import pytest
from pyformlang.regular_expression import Regex
from networkx import MultiDiGraph
from pyformlang.finite_automaton import State, Symbol
from project import regex_to_min_dfa, create_nfa
import random
import itertools

@pytest.fixture
def sample_graph():
    graph = MultiDiGraph()
    graph.add_edge(0, 1, label='a')
    graph.add_edge(1, 2, label='b')
    graph.add_edge(2, 3, label='c')
    graph.add_edge(3, 4, label='d')
    return graph

REGEX_TO_TEST = [
    "(aa)*",
    "a | a",
    "a* | a",
    "(ab) | (ac)",
    "(ab) | (abc)",
    "(abd) | (abc)",
    "(abd*) | (abc*)",
    "(abd)* | (abc)*",
    "((abd) | (abc))*",
    "a*a*",
    "a*a*b",
    "a* | (a | b)*",
    "a*(a | b)*",
    "(a | c)*(a | b)*",
]

class TestRegexToDfa:
    @pytest.mark.parametrize("regex_str", REGEX_TO_TEST, ids=lambda regex: regex)
    def test(self, regex_str: str) -> None:
        regex = Regex(regex_str)
        regex_cfg = regex.to_cfg()
        regex_words = regex_cfg.get_words()

        if regex_cfg.is_finite():
            all_word_parts = list(regex_words)
            word_parts = random.choice(all_word_parts)
        else:
            index = random.randint(0, 2**9)
            word_parts = next(itertools.islice(regex_words, index, None))

        word = list(map(lambda x: x.value, word_parts))

        dfa = regex_to_min_dfa(regex_str)

        minimized_dfa = dfa.minimize()
        assert dfa.is_deterministic()
        assert dfa.is_equivalent_to(minimized_dfa)
        assert dfa.accepts(word)

def test_create_nfa(sample_graph):
    start_states = {0}
    final_states = {4}
    nfa = create_nfa(sample_graph, start_states, final_states)
    assert all(isinstance(state, State) for state in nfa.states)
    assert all(isinstance(symbol, Symbol) for symbol in nfa.symbols)
    assert all(state in nfa.states for state in start_states)
    assert all(state in nfa.states for state in final_states)
    assert nfa.accepts("abcd") == True
    assert nfa.accepts("abc") == False
    assert nfa.accepts("ab") == False
    assert nfa.accepts("a") == False