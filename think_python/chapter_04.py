"""Chapter 4: Turtle graphics example - drawing a square."""
import turtle

# Create a turtle screen/window
SCREEN = turtle.Screen()
t = turtle.Turtle()

# Draw a square
t.forward(100)
t.left(90)
t.forward(100)
t.left(90)
t.forward(100)
t.left(90)
t.forward(100)

# Keep the window open until clicked
SCREEN.exitonclick()
