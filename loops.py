squares = [x**2 for x in range(4)]

for x in range(len(squares) - 1):
    for y in range(x+1,len(squares)):
        print(x, y, squares[x], squares[y])


