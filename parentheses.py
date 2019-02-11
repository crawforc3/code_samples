def convert_to_postfix(formula):
    stack = []
    new_formula = []
    for i,char in enumerate(formula):
        
        # Add numbers to posix formula
        if char not in operators:
            new_formula.append(char)
            
        # Add parentheses to stack
        elif char == '(':
            stack.append('(')            
        elif char == ')':
            # Move everything from the stack to the new_formula
            while stack[-1] != '(':
                #print(stack[-1])
                new_formula.append(stack.pop(-1))
            stack.pop(-1) # Remove the '(' for a blank stack
            
        # If not an operator, and not a prenthesis
        else:
            while stack \
                and stack[-1] != '(' \
                and order_of_operations[char] <= order_of_operations[stack[-1]]:
                new_formula.append(stack.pop(-1))
            stack.append(char)            
            
    # remaining
    while stack:
        new_formula.append(stack.pop(-1))
    return "".join(new_formula)



def convert_to_infix(formula):
    stack = []
    prev_op = None
    try:
        for char in formula:
            if char not in operators:
                stack.append(char)
            else:
                
                right = stack.pop()
                left = stack.pop()
                if prev_op and len(left) > 1 and order_of_operations[char] > order_of_operations[prev_op]:
                    # if previous operator has lower priority
                    # add '()' to the previous a
                    expr = '('+left+')' + char + right
                else:
                    expr = left + char + right
                stack.append(expr)
                prev_op = char
        return stack[-1]        
    except IndexError:
        print("\nWarning: This script doesn't handle negations")
        return None
            


if __name__ == "__main__":
    operators = ['+', '-', '*', '/', '(', ')']
    order_of_operations = {'+':1, '-':1, '*':2, '/':2}

    test_strings = ["1*(2+(3*(4+5)))", "x+(y+z)+(t+(v+w))", "2 + (3 / -5)"]

    for s in test_strings:    
        formula = s.replace(" ", "")
        convert_to_postfix(formula)
        post = convert_to_postfix(formula)
        print("\n",s, "\t> ", convert_to_infix(post))
