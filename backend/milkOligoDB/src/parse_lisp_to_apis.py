def parse_tokens(expression):
    tokens = []
    token = ''
    i = 0
    while i < len(expression):
        char = expression[i]
        if char == '(' or char == ')':
            if token:
                tokens.append(token)
                token = ''
            tokens.append(char)
            i += 1
        elif char == ' ':
            if token:
                tokens.append(token)
                token = ''
            i += 1
        else:
            token += char
            i += 1
    if token:
        tokens.append(token)
    return tokens

def process_expression(tokens, index, counter, operations):
    if tokens[index] != '(':
        # Atomic symbol
        return tokens[index], index + 1
    else:
        index += 1  # Skip '('
        func_name = tokens[index]
        index += 1
        args = []
        while tokens[index] != ')':
            if tokens[index] == '(':
                arg, index = process_expression(tokens, index, counter, operations)
                args.append(arg)
            else:
                args.append(tokens[index])
                index += 1
        index += 1  # Skip ')'
        counter[0] += 1
        identifier = f"#{counter[0]}"
        # Determine the operation
        if func_name == 'JOIN':
            relation = args[0]
            entity = args[1]
            if relation.endswith('_inv'):
                relation = relation[:-4]  # Remove '_inv'
                operation = f"https://icfoods-know.o18s.com/api/know/propositions/subject/{entity}/predicate/{relation}"
            else:
                operation = f"https://icfoods-know.o18s.com/api/know/propositions/object/{entity}/predicate/{relation}"
        elif func_name == 'AND':
            operation = f"AND({args[0]}, {args[1]})"
        elif func_name == 'COUNT':
            operation = f"COUNT({args[0]})"
        else:
            operation = f"{func_name.lower()}({', '.join(args)})"
        operations[identifier] = operation
        return identifier, index

def process_lisp_expression(expression):
    tokens = parse_tokens(expression)
    operations = {}
    counter = [0]  # Use list for mutable integer in nested function
    process_expression(tokens, 0, counter, operations)
    return operations