from typing import Any, Tuple, List, Dict, TypeVar, Set
from itertools import product
from datetime import datetime as dt

from pangu.language.errors import ExecutionError
from pangu.language.domain_language import predicate, DomainLanguage

"""
__init__ should take two inputs: first vocab (contains all entities, types and relations), second entities_in_utterance.
(Note that, in the following step to build ProductionRuleField from lambdaDCSLanguage, for actions generate those
entities_in_utterance, they are both global and linked actions, while the remaining are only global actions)
For most KBQA datasets, entities_in_utterance should simply be all tokens from the input utterance, however, in our
scenario, we might only consider the linked entities because entity linking is necessary.
"""

Unary = TypeVar('Unary')
Binary = TypeVar('Binary')


class GeneralKBLanguage(DomainLanguage):
    # TODO: distinguish entity and literal for general grammar
    # TODO: allow incremental update of constants to support linked_acitons (i.e., copy)
    def __init__(self):
        super().__init__({}, start_types=set([Unary, int]))
        # we will use sparql to interact with the KB instead of using the interpretation
        # defined by ourselves

        for t in [Binary, Unary]:
            def JOIN(a: Binary, b: t) -> t:
                results = set()
                if isinstance(b[0], tuple):
                    for v in product(a, b):
                        if v[0][1] == v[1][0]:
                            results.add((v[0][0], v[1][1]))

                elif isinstance(b[0], str):
                    for v in product(a, b):
                        if v[0][1] == v[1]:
                            results.add(v[0][0])
                else:
                    raise ExecutionError(f'The type of element in b is {type(b[0])}. '
                                         f'Not sure how you get here.')

                return list(results)

            self.add_predicate('JOIN', JOIN)

    @predicate
    def AND(self, u0: Unary, u1: Unary) -> Unary:
        a = set(u0)
        b = set(u1)
        return list(a.intersection(b))

    # @predicate
    # def JOIN(self, b1: Binary, b2: Binary) -> Binary:
    #     pass

    # @predicate
    # def JOIN(self, b: Binary, u: Unary) -> Unary:
    #     pass

    @predicate
    def COUNT(self, u: Unary) -> int:
        return len(u)

    @predicate
    def R(self, b: Binary) -> Binary:
        rtn = []
        for v in b:
            rtn.append((v[1], v[0]))
        return rtn

    @predicate
    def ARGMAX(self, u: Unary, b: Binary) -> Unary:
        maximum = float('-inf')
        arg = set()
        for v in product(u, b):
            if v[0] == v[1][0]:
                try:
                    value_string = v[1][1].split('^^')[0]
                    if value_string.__contains__('-'):
                        value = dt.strptime(value_string, '%Y-%m-%d')
                    else:
                        value = float(value_string)
                    if value > maximum:
                        maximum = value
                        arg = [v[0]]
                    elif value == maximum:
                        arg.append(v[0])

                except ValueError as error:
                    print("Not a numerical attribute:", error)

        return arg

    @predicate
    def ARGMIN(self, u: Unary, b: Binary) -> Unary:
        minimum = float('inf')
        arg = []
        for v in product(u, b):
            if v[0] == v[1][0]:
                try:
                    value_string = v[1][1].split('^^')[0]
                    if value_string.__contains__('-'):
                        value = dt.strptime(value_string, '%Y-%m-%d')
                    else:
                        value = float(value_string)
                    if value < minimum:
                        minimum = value
                        arg = [v[0]]
                    elif value == minimum:
                        arg.append(v[0])

                except ValueError as error:
                    print("Not a numerical attribute:", error)

        return arg

    @predicate
    def gt(self, b: Binary, u: Unary) -> Unary:
        results = set()
        for v in product(b, u):
            value_string = v[0][1].split("^^")[0]
            if value_string.__contains__('-'):
                value = dt.strptime(value_string, '%Y-%m-%d')
                comparison = dt.strptime(v[1].split["^^"][0], '%Y-%m-%d')
            else:
                value = float(value_string)
                comparison = float(v[1].split["^^"][0])

            if value > comparison:
                results.add(v[0][0])

        return list(results)

    @predicate
    def ge(self, b: Binary, u: Unary) -> Unary:
        results = set()
        for v in product(b, u):
            value_string = v[0][1].split("^^")[0]
            if value_string.__contains__('-'):
                value = dt.strptime(value_string, '%Y-%m-%d')
                comparison = dt.strptime(v[1].split["^^"][0], '%Y-%m-%d')
            else:
                value = float(value_string)
                comparison = float(v[1].split["^^"][0])

            if value >= comparison:
                results.add(v[0][0])

        return list(results)

    @predicate
    def lt(self, b: Binary, u: Unary) -> Unary:
        def gt(self, b: Binary, u: Unary) -> Unary:
            results = set()
            for v in product(b, u):
                value_string = v[0][1].split("^^")[0]
                if value_string.__contains__('-'):
                    value = dt.strptime(value_string, '%Y-%m-%d')
                    comparison = dt.strptime(v[1].split["^^"][0], '%Y-%m-%d')
                else:
                    value = float(value_string)
                    comparison = float(v[1].split["^^"][0])

                if value < comparison:
                    results.add(v[0][0])

            return list(results)

    @predicate
    def le(self, b: Binary, u: Unary) -> Unary:
        def gt(self, b: Binary, u: Unary) -> Unary:
            results = set()
            for v in product(b, u):
                value_string = v[0][1].split("^^")[0]
                if value_string.__contains__('-'):
                    value = dt.strptime(value_string, '%Y-%m-%d')
                    comparison = dt.strptime(v[1].split["^^"][0], '%Y-%m-%d')
                else:
                    value = float(value_string)
                    comparison = float(v[1].split["^^"][0])

                if value <= comparison:
                    results.add(v[0][0])

            return list(results)


if __name__ == '__main__':
    language = GeneralKBLanguage()
    print(language.all_possible_productions())
