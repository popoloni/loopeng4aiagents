# Controller-owned acceptance rules from the retained chapter 4 validation.
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(0, 0) == 0
assert add(10**30, 7) == 10**30 + 7
assert multiply(2, 3) == 6
assert multiply(-4, 5) == -20
assert multiply(0, 99) == 0
assert multiply(-7, -8) == 56
