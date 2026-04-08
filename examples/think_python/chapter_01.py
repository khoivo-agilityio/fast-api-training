"""Module providing a function printing python version."""

message = "Hello Python World!"
print(message)

message = "Hello Python Crash Course World!"
print(message)

floor_division_result = 84 // 2
cal_2 = 84 / 2
cal_3 = 84 % 2
cal_4 = abs(84 - 2)
cal_5 = floor_division_result << 99
cal_6 = 1_000_000

# exercise 1-2
# Python is ROUND TO EVEN
exercise1_2 = round(42.5)
exercise1_2_2 = round(42.5, 2)

print(exercise1_2)
print(exercise1_2_2)

# exercise 1-3
exercise1_3 = 2 + +2
print(exercise1_3)

exercise1_3_2 = round(42.5 / 4, 5)
print(exercise1_3_2)

# exercise 1-4

765  # int

2.718  # float

"2 pi"  # str

abs(-7)  # int

type(abs(-7.0))  # float

abs  # function

type(int)  # type

type(type)  # type

# exercise 1-5

# How many seconds are there in 42 minutes 42 seconds?
exercise1_5_1 = 42 * 60 + 42
print(exercise1_5_1)
# How many miles are there in 10 kilometers? Hint: there are 1.61 kilometers in a mile.
exercise1_5_2 = 10 / 1.61
print(exercise1_5_2)
# If you run a 10 kilometer race in 42 minutes 42 seconds,
# what is your average pace in seconds per mile?
exercise1_5_3 = (42 * 60 + 42) / 10 / 1.61
print(exercise1_5_3)
# What is your average pace in minutes and seconds per mile?
exercise1_5_4 = (42 * 60 + 42) / 10 / 1.61 / 60
print(exercise1_5_4)
# What is your average speed in miles per hour?
exercise1_5_5 = 10 / ((42 * 60 + 42) / 3600)
print(exercise1_5_5)
