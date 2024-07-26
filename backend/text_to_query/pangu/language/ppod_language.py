from typing import Collection, TypeVar

from pangu.language.domain_language import DomainLanguage, predicate

Entities = TypeVar('Entities', bound=Collection)
Classes = TypeVar('Classes', bound=Collection)
Property = TypeVar('Property')
NumericalProperty = TypeVar('NumericalProperty')
LiteralProperty = TypeVar('LiteralProperty')
Literals = TypeVar('Literals')


class PPODLanguage(DomainLanguage):
    def __init__(self):
        super().__init__({}, start_types={Entities})

        for p_t, o_t in [(Property, Entities), (LiteralProperty, Literals)]:
            def JOIN(p: p_t, o: o_t) -> Entities:
                pass

            self.add_predicate('JOIN', JOIN)

        # for t in [Entities, Classes]:
        #     def AND(set1: t, set2: Entities) -> Entities:
        #         pass
        #
        #     self.add_predicate('AND', AND)

    @predicate
    def AND(self, set1: Entities, set2: Entities) -> Entities:
        pass

    @predicate
    def COUNT(self, e: Entities) -> int:
        pass

    # @predicate
    # def LT(self, p: NumericalProperty, c: Classes) -> Entities:
    #     pass
    #
    # @predicate
    # def GT(self, p: NumericalProperty, c: Classes) -> Entities:
    #     pass
    #
    # @predicate
    # def LE(self, p: NumericalProperty, c: Classes) -> Entities:
    #     pass
    #
    # @predicate
    # def GE(self, p: NumericalProperty, c: Classes) -> Entities:
    #     pass
    #
    # @predicate
    # def ARGMIN(self, c: Classes, p: NumericalProperty) -> Entities:
    #     pass
    #
    # @predicate
    # def ARGMAX(self, c: Classes, p: NumericalProperty) -> Entities:
    #     pass


if __name__ == '__main__':
    language = PPODLanguage()
    print(language.all_possible_productions())
