from pyformlang.regular_expression import Regex
from pyformlang.finite_automaton import EpsilonNFA, DeterministicFiniteAutomaton

def regex_to_min_dfa(regex: str) -> DeterministicFiniteAutomaton:
    regex = Regex(regex)
    nfa = regex.to_epsilon_nfa()
    dfa = nfa.to_deterministic()
    min_dfa = dfa.minimize()
    
    return min_dfa

min_dfa = regex_to_min_dfa("a*b|b*")
print(min_dfa)

