#Parentheses removal function. Given a string containing an expression, return the expression with unnecessary parentheses removed.
#For example:
# 1*(2+(3*(4+5))) ===> "1*(2+3*(4+5))"
# "2 + (3 / -5) ===> "2 + 3 / -5"
# x+(y+z)+(t+(v+w)) ===> "x+y+z+t+v+w"


s = input("Enter your formula: ")
print("You entered " + str(s))

# Map the parentheses to string elements
mapper = {}
for i,thing in enumerate(s):
    if thing == '(':
        mapper[i] = thing
    if thing == ')':
        mapper[i] = thing

# how many pairs of parentheses?
pairs = len(mapper)//2

# For each pair of parentheses, Pop them out and evaluate against original forumla
# if output of new formula == old formula, pop out the next pair of parentheses
# if output of new formula != old formula, put parentheses back and try the next pair
# Repeat for all pairs of parentheses 
formula = list(s)
for i in range(pairs):
    #print("".join(formula))
    test = list(formula)
    
    left = list(mapper.keys())[pairs-i-1] 
    right = list(mapper.keys())[pairs+i] -i -1
    #print(formula[left], formula[right])
    
    test.pop(left)
    test.pop(right) 
    
    answer = eval("".join(test))
    #print("".join(test), "=", answer)
    
    if eval("".join(test)) == eval("".join(formula)):
        formula.pop(left)
        formula.pop(right)
        #print("".join(formula))

print("Improved formula:", "".join(formula), "=", eval("".join(formula)))