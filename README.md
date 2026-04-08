# FastAPI Training Plan

## **Feb 02, 2026**

# **OVERVIEW**

This training is designed to help learners move from Python basics to building production‑ready FastAPI services. It focuses on correct API design, async mindset, validation, persistence, security, and best practices commonly used in real-world backend systems.

## **PREREQUISITES**

**General**

* Basic knowledge of Python programming.

* Familiarity with web development concepts such as HTTP, client-server architecture, and databases.

* **Important**: Please walk through the [ACCELERATE LEARNING WITH AI ASSISTANCE](https://docs.google.com/document/d/1vrHTP0oUX39HoLSHbA-oU69TQCLTRWNbFTbcgRNKIh4/edit?usp=sharing) section to get a quick overview of how to use AI to learn more efficiently and effectively.

**Environment**

* [Python 3.13](https://www.python.org/)\+

* [Package manager: uv](https://docs.astral.sh/uv/)

* [Linter and formatted: Ruff](https://docs.astral.sh/ruff/)

* [Pre-commit](https://pre-commit.com/) hook: [Ruff](https://github.com/astral-sh/ruff-pre-commit)

* [Type checker: ty](https://docs.astral.sh/ty/)

**Extension suggestions**

* [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

* [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)

* [Python Docstring Generator](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring)

* [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

## **TIMELINE**

**Total: 31 days**

* API Design: **2 days**

* Database Design: **1 day**

* Basic: **5 days**

* Intermediate: **8 days**

* Advanced: **7 days**

* Final practice: **8 days**

## **OBJECTIVES**

* Build RESTful APIs using FastAPI

* Design clean request/response models with Pydantic

* Work with async endpoints and understand performance implications

* Implement CRUD operations with databases

* Secure APIs with authentication and authorization

* Write tests and maintain clean, scalable code

* Use FastAPI’s automatic documentation effectively

# **API DESIGN**

**Objective**: To familiarize yourself with APIs and understand RESTful API principles, focusing on HTTP methods and best practices for designing efficient and scalable APIs.

**Timeline**: **2 days**

## **1\. An introduction to APIs**

* [API introduction](https://zapier.com/resources/guides/apis/introduction)

* [API protocols](https://zapier.com/resources/guides/apis/protocols)

* [API types and formats](https://zapier.com/resources/guides/apis/data-formats)

* [API authentication, part 1: Basic vs. key](https://zapier.com/resources/guides/apis/authentication-part-1)

* [API design](https://zapier.com/resources/guides/apis/design)

* [API implementation](https://zapier.com/resources/guides/apis/implementation)

## **2\. RESTful web API design**

* [What is REST?](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#what-is-rest)

* [Organize the API design around resources](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#organize-the-api-design-around-resources)

* [Define API operations in terms of HTTP methods](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#define-api-operations-in-terms-of-http-methods)

* [Conform to HTTP semantics](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#conform-to-http-semantics)

* [Filter and paginate data](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#filter-and-paginate-data)

* [Versioning a RESTful web API](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#versioning-a-restful-web-api)

* [Open API Initiative](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design#open-api-initiative)

## **3\. Optional: The Design of Web APIs [eBook](https://drive.google.com/file/d/1cJ1A5PwRybD2d5oyOR1qOWowQrBu6H2T/view?usp=sharing)**

# **DATABASE DESIGN**

**Objective**: Understand how to structure data correctly by learning how to model tables, relationships, and constraints based on examples.

**Timeline**: **1 day**

**References:**

* [ER Diagram Cheat Sheet](https://www.red-gate.com/blog/er-diagram-cheat-sheet)

# **BASIC (Foundation \- Build & Understand APIs)**

## **Chapter 1: Introduction to FastAPI**

**Description**: Introduces FastAPI, its ecosystem, and why it is a strong choice for modern APIs.

**Objectives**

* Understand what FastAPI is and where it fits

* Set up a local development environment

* Run a simple FastAPI application

**Topics**

* What FastAPI is & why use it: [FastAPI Overview](https://fastapi.tiangolo.com/), [Features](https://fastapi.tiangolo.com/features/), [Tutorial Introduction](https://fastapi.tiangolo.com/tutorial/)

* Setting up your FastAPI app and endpoints: [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)

## **Chapter 2: Basic Routing & Request Handling**

**Description**: Covers the core mechanics of handling HTTP requests and responses.

**Objectives**

* Define API endpoints correctly

* Handle different request inputs

* Return proper responses and errors

**Topics**

* [Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/), [Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/), [Header Parameters](https://fastapi.tiangolo.com/tutorial/header-params/)

* [Request Body](https://fastapi.tiangolo.com/tutorial/body/), JSON data, [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)

* [Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/), [Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)

## **Chapter 3: Data Validation & Models**

**Description**: Focuses on using Pydantic to validate input and control output.

**Objectives**

* Create reliable data contracts

* Validate input automatically

* Control response shape and serialization

**Topics**

* Using Pydantic for request/response models

  * [Body \- Multiple Parameters / Fields / Nested Models](https://fastapi.tiangolo.com/tutorial/body-multiple-params/)

  * [Extra Models](https://fastapi.tiangolo.com/tutorial/extra-models/)

* Input validation, output serialization

  * [Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)

  * [Path Parameters and Numeric Validations](https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/)

* [Custom exceptions and validation errors](https://fastapi.tiangolo.com/tutorial/handling-errors/#override-the-default-exception-handlers)

***Exercise 1**: in-memory CRUD API with rich validation and interactive docs.*

# **INTERMEDIATE (Production-Ready APIs)**

## **Chapter 4: Database Integration & CRUD**

**Description**: Applies models and async knowledge to real data persistence.

**Objectives**

* Connect FastAPI to databases

* Design CRUD APIs

* Understand ORM usage

**Topics**

* [Relational databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) (SQL, ORM like SQLAlchemy)

* Writing CRUD operations, migrations

## **Chapter 5: Authentication, Authorization & Security**

**Description**: Secures APIs after core data flows are understood.

**Objectives**:

* Protect endpoints

* Implement authentication flows

* Follow security best practices

**Topics:**

* JWT tokens, OAuth2 flows

  * [OAuth2 with Password (Bearer with JWT tokens)](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

* API keys and role-based access

  * [Security \- First Steps](https://fastapi.tiangolo.com/tutorial/security/first-steps/)

  * [Get Current User](https://fastapi.tiangolo.com/tutorial/security/get-current-user/)

* Secure endpoints, middleware

  * [CORS](https://fastapi.tiangolo.com/tutorial/cors/)

  * [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

## **Chapter 6: Testing Fundamentals**

**Description**: Introduces testing as a core development skill, ensuring APIs are reliable, correct, and safe to change.

**Objectives**

* Writing basic API tests

* Understanding TestClient

* Testing request/response contracts

**Topics**

* [FastAPI TestClient](https://fastapi.tiangolo.com/tutorial/testing/)

* Basic pytest structure

* Testing CRUD endpoints

* Testing auth-protected routes

***Exercise 2**: authenticated, database-backed CRUD API with protected routes, add basic unit tests.*

# **ADVANCED (Production Polish & Best Practices)**

## **Chapter 7: Asynchronous Programming & Performance**

**Description**: Introduces async concepts early to build correct mental models.

**Objectives**

* Understand async vs sync endpoints

* Avoid common performance pitfalls

* Use ASGI servers properly

**Topics**

* [Async vs sync endpoints](https://fastapi.tiangolo.com/async/)

* [Using fast ASGI servers](https://fastapi.tiangolo.com/deployment/server-workers/)

## **Chapter 8: Advanced Features & Real‑Time Functionality**

**Description**: Adds background processing and real-time capabilities.

**Objectives**

* Handle long‑running tasks

* Implement real‑time APIs

**Topics**

* [Background tasks, scheduling jobs](https://fastapi.tiangolo.com/tutorial/background-tasks/)

* [WebSockets for real‑time communication](https://fastapi.tiangolo.com/advanced/websockets/)

## **Chapter 9: Debugger, Monitoring & Best Practices**

**Description**: Focuses on diagnosing issues, observing system behavior, and applying best practices to keep FastAPI services stable, maintainable, and production-ready.

**Objectives**

* Debug FastAPI applications effectively

* Add basic monitoring and logging

* Apply best practices for long-term maintainability

**Topics**

* [Debugging FastAPI applications](https://fastapi.tiangolo.com/tutorial/debugging/)

* Logging, metrics, and basic monitoring concepts

* Best practices: clean architecture, dependency injection, configuration

  * [Bigger Applications \- Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)

  * [Advanced Dependencies](https://fastapi.tiangolo.com/advanced/advanced-dependencies/)

## **Chapter 10:  Documentation & Developer Experience**

**Description**: Polishes APIs for teams and long-term collaboration by leveraging FastAPI’s automatic documentation and developer-friendly features.

**Objectives**:

* Use built-in API documentation effectively

* Manage API evolution safely

* Improve developer productivity and onboarding

**Topics**

* Automatic docs: Swagger UI, ReDoc

  * [Metadata and Docs URLs](https://fastapi.tiangolo.com/tutorial/metadata/)

  * [Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/#tags-with-enums)

* Developer productivity

  * [Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)

  * [Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

**Exercise 3**: clean architect, structured logs, rich docs, settings, lifespan events, live deployment.

# **PRACTICE**

[\[KhoiVo\] FastAPI Practice](https://docs.google.com/document/d/1Q1zBMAvUV5L2SzRMgzqNvx9gxdJoen-gDiDCNsZB02Q/edit?usp=sharing)