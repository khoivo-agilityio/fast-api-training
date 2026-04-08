# FastAPI Practice

## **Mar 05, 2026**

# **OVERVIEW**

## **PURPOSE**

This assignment evaluates your ability to design, implement, secure, test, and prepare for deployment a real-world backend system using FastAPI.

You must demonstrate understanding across:

* RESTful API design  
* Data modeling and persistence  
* Authentication and authorization  
* Async programming  
* Background processing  
* Real-time communication  
* Testing  
* Logging and monitoring  
* Clean architecture  
* Deployment preparation

## **TIMELINE**

**Total: ?**

# **REQUIREMENT**

1. ## **Project Description**

You are required to build a Collaborative Project & Task Management API, similar in concept to tools like Trello or Jira.

The system must support:

* Multi-user accounts  
* Project management  
* Task tracking  
* Commenting  
* Role-based permissions  
* Real-time notifications  
* Production-ready configuration

The application must be fully backend (API only).

2. ## **Technical Requirements**

Mandatory:

* Python  
* FastAPI  
* Pydantic  
* SQLAlchemy (ORM)  
* PostgreSQL  
* Alembic (migrations)  
* JWT Authentication  
* pytest  
* Docker (optional)

Recommended:

* Async SQLAlchemy  
* Uvicorn / Gunicorn  
* Ruff (linting)  
* ty (type checking)

3. ## **Functional Requirements**

1. ### **API Design**

Base URL must be versioned: /api/v1/

RESTful resource-based endpoints:

* /users  
* /projects  
* /tasks  
* /comments

Must Implement

* Proper HTTP methods  
* Correct status codes  
* Pagination (limit, offset)  
* Filtering  
* Sorting  
* API versioning strategy  
* Structured error responses

2. ### **Database Design**

You must design relational database schema including:

* Entities  
* User  
* Project  
* ProjectMember  
* Task  
* Comment

Requirements

* Primary keys  
* Foreign keys  
* Indexes  
* Unique constraints  
* Proper relationships (1-N, N-N)  
* Alembic migrations  
* ER Diagram (submitted)

3. ### **Authentication & Authorization**

You must implement:

* OAuth2 Password flow  
* JWT access tokens  
* Refresh token mechanism  
* Password hashing (bcrypt)  
* Role-Based Access Control (RBAC)

Roles

* Admin  
* Project Manager  
* Member

Permission Examples

* Only project members can view tasks  
* Only managers can add/remove members  
* Only task owner or manager can modify task  
* Only admin can delete projects

4. ### **CRUD Operations**

Users

* Register  
* Login  
* Get current user  
* Update profile

Projects

* Create project  
* Add/remove members  
* List user projects

Tasks

* Create task  
* Assign user  
* Update status  
* Delete task

Comments

* Create comment  
* List task comments

All endpoints must:

* Use Pydantic request/response models  
* Validate input  
* Return consistent responses  
* Handle errors properly

5. ### **Asynchronous Programming**

You must demonstrate:

* Async endpoints  
* Async DB session  
* Proper non-blocking operations  
* Avoid blocking calls inside async routes

Provide explanation in README:

* Difference between sync and async  
* When to use each

6. ### **Background Tasks**

Implement background task handling for:

* Simulated email notification when:  
  * Task assigned  
  * Project created

Use FastAPI BackgroundTasks.

7. ### **WebSockets (Real-Time)**

Implement: /ws/notifications

Requirements:

* Notify assigned user when task status changes  
* Support multiple connected users  
* Handle disconnect properly

8. ### **Middleware & Cross-Cutting Concerns**

Must include:

* Logging middleware  
* Request ID middleware  
* CORS configuration  
* Execution time measurement

9. ### **Testing**

Use pytest.

Minimum requirements:

* Test registration and login  
* Test protected endpoints  
* Test full CRUD lifecycle  
* Test invalid input handling  
* Test permission denial cases

Minimum coverage: 80%

Testing must use separate test database.

10. ### **Logging & Monitoring**

You must implement:

* Structured logging (JSON format)  
* Log levels (INFO, WARNING, ERROR)  
* Error logging  
* Request tracing via request\_id

Explain in README:

* How logs could integrate with centralized logging systems

11. ### **Clean Architecture**

Your project must follow modular and maintainable structure.

Required separation:

* Routers  
* Services  
* Repository layer  
* Schemas  
* Models  
* Core (config, security)  
* Dependencies  
* Tests

Documentation & Developer Experience

You must:

* Customize Swagger metadata  
* Organize endpoints by tags  
* Provide example request bodies  
* Provide complete README including:  
  * Setup instructions  
  * Environment variables  
  * Running the app  
  * Running tests  
  * Docker usage (optional)

12. ### **Deployment Readiness**

Must include:

* 3rd service configuration if any  
* Production settings  
* Environment configuration (.env.example)  
* Health check endpoint /health

Bonus (optional):

* Gunicorn \+ Uvicorn worker configuration

4. ## **Non-Functional Requirements**

* Code must be linted and formatted  
* Strong typing required  
* Clear naming conventions  
* Clean commit history  
* No hardcoded secrets  
* Secure configuration handling

5. ## **Deliverables**

You must submit:

* GitHub repository  
* ER Diagram  
* README documentation  
* Test coverage report (\>=80%)  
* API documentation screenshot
