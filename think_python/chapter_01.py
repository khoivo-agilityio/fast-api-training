"""Module providing a function printing python version."""

MSG = "Hello Python World!"
print(MSG)

MSG = "Hello Python Crash Course World!"
print(MSG)

CAL1 = 84//2
CAL2 = 84/2
CAL3 = 84%2
CAL4 = abs(84-2)
CAL5 = CAL1 << 99
CAL6 = 1_000_000

# exercise 1-2
# Python is ROUND TO EVEN
EXERCISE1_2 = round(42.5)
EXERCISE1_2_2 = round(42.5, 2)

print(EXERCISE1_2)
print(EXERCISE1_2_2)

# exercise 1-3
EXERCISE1_3 = 2++2
print(EXERCISE1_3)

EXERCISE1_3_2 = round(42.5/4,5)
print(EXERCISE1_3_2)

# exercise 1-4

765 # int

2.718 # float

'2 pi' # str

abs(-7) # int

type(abs(-7.0)) # float

abs # function

type(int) # type

type(type) # type

# exercise 1-5

#How many seconds are there in 42 minutes 42 seconds?
EXERCISE1_5_1 = 42*60 + 42
print(EXERCISE1_5_1)
#How many miles are there in 10 kilometers? Hint: there are 1.61 kilometers in a mile.
EXERCISE1_5_2 = 10/1.61
print(EXERCISE1_5_2)
# If you run a 10 kilometer race in 42 minutes 42 seconds, 
# what is your average pace in seconds per mile?
EXERCISE1_5_3 = (42*60 + 42)/10/1.61
print(EXERCISE1_5_3)
#What is your average pace in minutes and seconds per mile?
EXERCISE1_5_4 = (42*60 + 42)/10/1.61/60
print(EXERCISE1_5_4)
#What is your average speed in miles per hour?
EXERCISE1_5_5 = 10/((42*60 + 42)/3600)
print(EXERCISE1_5_5)
