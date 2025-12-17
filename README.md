# Python Training Plan

**_Dec 17, 2025_**

## **OVERVIEW**

This training plan focuses on building core Python programming skills, emphasizing problem-solving, coding best practices, and foundational concepts. Ensuring a well-rounded learning experience through practical exercises, coding tasks, and unit testing.

## **PREREQUISITES**

### **General**

- Understanding basic programming concepts like loops, variables, and conditionals is helpful.

- Basic knowledge of web development.

- **Important**: Please walk through the [ACCELERATE LEARNING WITH AI ASSISTANCE](https://docs.google.com/document/d/1vrHTP0oUX39HoLSHbA-oU69TQCLTRWNbFTbcgRNKIh4/edit?usp=sharing) section to get a quick overview of how to use AI to learn more efficiently and effectively.

### **Environment**

- [Python 3.13](https://www.python.org/)

- [Package manager: uv](https://docs.astral.sh/uv/)

- [Linter and formatted: Ruff](https://docs.astral.sh/ruff/)

- [Pre-commit](https://pre-commit.com/) hook: [Ruff](https://github.com/astral-sh/ruff-pre-commit)

### **Extension suggestions**

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

- [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)

- [Python Docstring Generator](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring)

- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

## **TIMELINE**

### **Total: 20 days**

- Python Fundamentals: **10 days**

- Deep Dive into Python: **10 days**

## **OBJECTIVES**

- **Core Syntax & Concepts:** Learn Python's basic data types, control structures, functions, and error handling.

- **Problem Solving**: Develop algorithms, debug code, and optimize for efficiency.

- **Data Structures & File Handling**: Understand lists, dictionaries, tuples, and file operations.

- **Typing**: Understand and apply Python's typing system \- support for type hints.

- **Unit Testing**: Learn writing tests, and focus on Test-Driven Development (TDD).

- AI assistance: Leverage AI tools for enhanced learning and development; automate the generation of unit tests, improving code coverage and testing efficiency.

## **PYTHON FUNDAMENTALS**

**Objective**: Focus on core concepts like data types, functions, and loops, progressing to advanced topics such as recursion and object-oriented programming. It emphasizes hands-on learning with exercises, promoting problem-solving and Pythonic coding practices.

## **Timeline: 10 days**

## **Official document:** [Think Python](https://allendowney.github.io/ThinkPython/index.html)

## **Part 1: Core Concepts**

- [Chapter 1:](https://allendowney.github.io/ThinkPython/chap01.html) The Way of the Program \- Introduction to programming principles and Python setup.

- [Chapter 2](https://allendowney.github.io/ThinkPython/chap02.html): Variables and Statements \- Learn about data types, variables, and simple expressions.

- [Chapter 3](https://allendowney.github.io/ThinkPython/chap03.html): Functions \- Define and use functions.

- [Chapter 5](https://allendowney.github.io/ThinkPython/chap05.html): Conditionals and Recursion \- Apply conditionals and understand recursion.

- [Chapter 6](https://allendowney.github.io/ThinkPython/chap06.html): Return values

- [Chapter 7](https://allendowney.github.io/ThinkPython/chap07.html): Iteration and Search \- Use loops for repetitive tasks.

## **Part 2: Data Structures & Files**

- [Chapter 8](https://allendowney.github.io/ThinkPython/chap08.html): Strings and Regular Expressions \- Work with strings, methods, slicing, and Regular Expressions.

- [Chapter 9](https://allendowney.github.io/ThinkPython/chap09.html): Lists \- Use lists for managing data collections.

- [Chapter 10](https://allendowney.github.io/ThinkPython/chap10.html): Dictionaries \- Store and retrieve key-value pairs using dictionaries.

- [Chapter 11](https://allendowney.github.io/ThinkPython/chap11.html): Tuples \- Explore tuples for immutable data storage and unpacking techniques.

- [Chapter 12](https://allendowney.github.io/ThinkPython/chap12.html): Text Analysis and Generation

- [Chapter 13](https://allendowney.github.io/ThinkPython/chap13.html): Files and Databases

## **Part 3: Object-Oriented Programming (OOP) & Extras**

- [Chapter 14](https://allendowney.github.io/ThinkPython/chap14.html): Classes and Functions \- Learn how functions interact with classes, including method definitions.

- [Chapter 15](https://allendowney.github.io/ThinkPython/chap15.html): Classes and Methods \- Define and use class methods, instance methods, and object behaviors.

- [Chapter 16](https://allendowney.github.io/ThinkPython/chap16.html): Classes and Objects \- Get introduced to object-oriented programming by defining custom classes.

- [Chapter 17](https://allendowney.github.io/ThinkPython/chap17.html): Inheritance \- Explore how to extend classes using inheritance for code reuse.

- [Chapter 18](https://allendowney.github.io/ThinkPython/chap18.html). Python Extras \- Learn more about Sets, helpful built-in methods, and debugging skills.

## **DEEP DIVE INTO PYTHON**

**Objective**: Focus on mastering idiomatic Python code, along with important practices like type annotations and unit testing.

**Timeline**: 10 days

## **Writing Idiomatic Python 3 (3 days)**

**Objective**: Learn to write clean, efficient, and Pythonic code by following best practices in control structures, data handling, and code organization, improving readability and maintainability.

**Ebook**: [Writing Idiomatic Python 3](https://drive.google.com/file/d/1qSTs6k7KsciEn2rwvTV16TYFkk2hM4hO/view?usp=sharing).

- **Chapter 1: Control Structures and Functions** \- This chapter focuses on improving Python code readability and efficiency by utilizing Pythonic approaches. Topics include If statements, for loops, and functions.

- **Chapter 2: Working with Data** \- This chapter covers best practices for manipulating data types such as lists, dictionaries, strings, and sets. Key points include Lists, dictionaries, strings, classes, and generators.

- **Chapter 3: Organizing Your Code** \- Focuses on code organization and modularity, encouraging simplicity and clarity. Topics include Modules, formatting, executable scripts, and imports.

- **Chapter 4: General Advice** \- Provides general Python programming advice for maintaining efficient, readable, and robust code: Avoid Reinventing the Wheel and Learn Key Modules.

## **Typing (1 day)**

**Objective**: Learn to use type hints to improve code clarity, readability, and maintainability, ensuring better static type checking and function annotations in Python.

**Official document**: [Typing](https://docs.python.org/3/library/typing.html).

- **Basic Types**: Understand the usage of fundamental types like int, str, and None for basic function annotations.

- **Collections**: Learn how to annotate collections such as List, Dict, and Set for more complex data types.

- **Generics**: Work with TypeVar and Generic to create flexible and reusable functions or classes.

- **Callables**: Use Callable to define the types of functions that take specific argument types and return a value.

- **Union & Optional**: Annotate variables that can have multiple types using Union or indicate optional values with Optional.

- **Type Aliases**: Define custom names for types with TypeAlias for clarity and reuse in the code.

- **Literal Types**: Restrict the values a variable can take using Literal for specific, predefined values.

- **Typed Dict**: Use TypedDict to specify dictionaries with fixed keys and their associated types.

## **Unit testing in Python (4 days)**

**Objective**: Learn how to use Python’s unittest framework to write and manage tests. Focus on key concepts like creating test cases, making assertions, and organizing tests. Improve code reliability with tools like mocking, test discovery, and skipping tests for more effective debugging and software maintenance.

**Introduction**: [Introduction to Test-Driven Development (TDD)](https://agiledata.org/essays/tdd.html).

**Official document**: [unitest \- Unit testing framework](https://docs.python.org/3/library/unittest.html).

- **Introduction**: Learn the basics of **unittest** framework, including test cases, suites, and runners.

- **Writing Tests**: Write test methods with assertions and use setUp/tearDown for preparation.

- **Running Tests**: Automate test execution with discovery and command-line/IDE runners.

- **Organizing Tests**: Group tests into suites for better organization.

- **Advanced Features**: Use mocking and skipping tests to handle complex scenarios.

**Reference**: [Writing Unit Tests for Your Code](https://realpython.com/python-unittest/).

## **Exercise (2 days)**

Refactor previous sample and exercise code by applying best practices, adding type hints, and writing unit tests to ensure code reliability and clarity.

## **ADDITIONAL TOOLS AND TOPICS**

- [What’s New In Python 3.11](https://docs.python.org/3/whatsnew/3.11.html)

- [What’s New In Python 3.12](https://docs.python.org/3/whatsnew/3.12.html)

- [What’s New In Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)

- [Real Python Tutorials](https://realpython.com/)

- [Python Debugging](https://code.visualstudio.com/docs/python/debugging)
