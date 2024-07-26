from collections import defaultdict

import re
from typing import List, Dict

NUMBER_CHARACTERS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "-"}
MONTH_NUMBERS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}
ORDER_OF_MAGNITUDE_WORDS = {"hundred": 100, "thousand": 1000, "million": 1000000}
NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    **MONTH_NUMBERS,
}


def split_string_without_square_brackets(s):
    pattern = r'\[[^\]]*\]'
    matches = re.findall(pattern, s)
    for match in matches:
        s = s.replace(match, match.replace(' ', '<SPACE>'))
    # parts = re.split(r'\s+', s)
    parts = s.split()
    parts = [part.replace('<SPACE>', ' ') for part in parts]
    return parts


def lisp_to_nested_expression(lisp_string: str) -> List:
    """
    Takes a logical form as a lisp string and returns a nested list representation of the lisp.
    For example, "(count (division first))" would get mapped to ['count', ['division', 'first']].
    """
    stack: List = []
    current_expression: List = []
    tokens = split_string_without_square_brackets(lisp_string)
    for token in tokens:
        while token[0] == "(":
            nested_expression: List = []
            current_expression.append(nested_expression)
            stack.append(current_expression)
            current_expression = nested_expression
            token = token[1:]
        current_expression.append(token.replace(")", ""))
        while token[-1] == ")":
            current_expression = stack.pop()
            token = token[:-1]
    return current_expression[0]


def linearize_lisp_expression(expression: list, sub_formula_id):
    sub_formulas = []
    for i, e in enumerate(expression):
        if isinstance(e, list) and e[0] != 'R':
            sub_formulas.extend(linearize_lisp_expression(e, sub_formula_id))
            expression[i] = '#' + str(sub_formula_id[0] - 1)

    sub_formulas.append(expression)
    sub_formula_id[0] += 1
    return sub_formulas


def linearize_lisp_expression_for_bottom_up(expression: list, sub_formula_id):
    sub_formulas = []
    level = {}
    max_sub_level = -1
    for i, e in enumerate(expression):
        # if isinstance(e, list) and e[0] != 'R':
        if isinstance(e, list):
            sf, lvl = linearize_lisp_expression_for_bottom_up(e, sub_formula_id)
            sub_formulas.extend(sf)
            level.update(lvl)
            expression[i] = '#' + str(sub_formula_id[0] - 1)
            if lvl[sub_formula_id[0] - 1] > max_sub_level:
                max_sub_level = lvl[sub_formula_id[0] - 1]
    current_level = max_sub_level + 1

    sub_formulas.append(expression)

    level[sub_formula_id[0]] = current_level
    sub_formula_id[0] += 1

    return sub_formulas, level


def get_sub_programs(formula: str):
    expression = lisp_to_nested_expression(formula)

    # level_mapping: sub_formula_id -> level
    sub_formulas, level_mapping = linearize_lisp_expression_for_bottom_up(expression, [0])

    new_level_mapping = defaultdict(lambda: [])
    for k, v in level_mapping.items():
        new_level_mapping[v].append(k)

    return sub_formulas, new_level_mapping


def fill_sub_programs(sub_programs: List, entity_name: Dict = {}, use_mid=False):
    """
    Replace all references (e.g., #0, #1) with corresponding programs
    :param sub_programs: sub_programs to be processed
    :param entity_name: a dictionary maps an entity ID to an entity mention;this may only be necessary for KBQA
    :param use_mid: Also only for KBQA. Indicates whether to use an entity ID or an entity mention
    :return:
    """
    sub_programs_filled = []
    for i, p in enumerate(sub_programs):
        p = [*p]
        for j, expression in enumerate(p):
            if expression[0] == '#':
                sub_id = int(expression[1:])
                p[j] = sub_programs_filled[sub_id]
            if not use_mid:
                if expression.__contains__('^^'):
                    p[j] = p[j].split('^^')[0]
                if expression in entity_name:
                    p[j] = entity_name[expression]

        sub_programs_filled.append(f"({' '.join(p)})")

    return sub_programs_filled


def get_level_wise_supervision(formula: str):
    sub_formulas, level_mapping = get_sub_programs(formula)
    processed_formulas = fill_sub_programs(sub_formulas)

    level_wise_programs = []
    for i in range(len(level_mapping)):
        level_wise_programs.append([processed_formulas[j] for j in level_mapping[i]])

    return level_wise_programs


if __name__ == '__main__':
    program = "(AND XXX (JOIN relation2 (AND (JOIN relation1 x1) (JOIN relation0 x0))))"
    sub_formulas, new_level_mapping = get_sub_programs(program)
    for sub_formula in sub_formulas:
        print(f"({' '.join(sub_formula)})")
    # key: height; value: a list of subprograms (denoted with the indices in sub_formulas)
    print(new_level_mapping)

    processed_formulas = fill_sub_programs(sub_formulas, {})
    print(processed_formulas)

    print(get_level_wise_supervision(program))
