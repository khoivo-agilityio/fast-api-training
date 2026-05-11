![][image1]

www.agilityio.com

# Big Practice

## **April 20, 2026**

# **OVERVIEW**

## **Project Overview**

The goal of this project is to build a backend system for an AI-Enhanced Learning Platform.

The platform allows instructors to create courses and lessons, students to enroll in courses, complete quizzes or assignments, and track learning progress.

**Project**: AI-Enhanced Learning Platform

**Duration**: ?

**Technology Stack**:

* Python  
* FastAPI  
* Pydantic  
* SQLAlchemy (ORM)  
* PostgreSQL  
* Alembic (migrations)  
* JWT Authentication  
* pytest  
* Docker  
* RailWay

## **Project Functional Overview**

The system must support three main roles:

* Admin: Platform administrator managing the system.  
* Instructor: Creates courses, lessons, and assignments.  
* Student: Enrolls in courses, studies content, and completes quizzes.

# **REQUIREMENT**

## **Core Platform Development**

1. ### **Objective**

Build the backend system of an AI-Enhanced Learning Platform using FastAPI.

Participants must design and implement the data models, APIs, and application logic required to support course management, learning activities, and student progress tracking.

2. ### **System Architecture**

The project should be organized into modular components (routers, services, repositories, and schemas) to ensure modularity and maintainability.

Typical functional areas include:

* User management  
* Course management  
* Lesson management  
* Quiz or assessment management  
* Learning progress tracking  
* Submission or answer handling

Participants should design the project structure following FastAPI best practices, ensuring clear separation of responsibilities between modules (e.g., routers for endpoints, services for business logic, repositories for data access, and schemas for validation).

3. ### **Database Design**

Participants must design the database schema before implementing the system.

The platform should support the following core entities and relationships:

* Users interacting with the platform  
* Courses created and managed by instructors  
* Lessons belonging to courses  
* Students enrolling in courses  
* Quizzes or assessments associated with lessons  
* Student submissions or answers to quizzes  
* Student progress tracking across lessons or courses

The database must include appropriate relationships, such as:

* One-to-many relationships (e.g., courses and lessons)  
* Many-to-many relationships (e.g., students enrolling in courses)  
* Relationships between quizzes, questions, and submissions

Participants are responsible for determining:

* Model fields  
* Constraints  
* Relationship types  
* Data validation rules

An ER diagram must be created before implementing models.

4. ### **API Development**

Participants must expose the system functionality through RESTful APIs using FastAPI.

The APIs should support the main platform workflows, including:

* User authentication and identification  
* Course discovery and management  
* Lesson access and content retrieval  
* Quiz or assessment participation  
* Submission of answers or assignments  
* Tracking and retrieving learning progress

API design should follow RESTful principles and make appropriate use of FastAPI components such as Pydantic schemas, dependency injection, path operations, and APIRouter.

Participants must decide how to structure endpoints and responses.

5. ### **DRF Features Usage**

The implementation should demonstrate practical use of key FastAPI concepts, including:

* Pydantic models (schemas) for request validation and response serialization  
* Dependency injection for shared logic (e.g., database sessions, current user)  
* APIRouter for organizing endpoints into modular route groups  
* OAuth2 with JWT tokens for authentication and role-based permission control  
* Query parameters, filtering, and pagination for resource collections  
* Proper HTTP status codes and structured error handling with HTTPException

Participants should configure FastAPI settings appropriately for the project (e.g., CORS middleware, lifespan events, environment-based configuration).

6. ### **Admin features**

Participants should implement admin-level API endpoints to support basic platform management.

Administrative capabilities should include managing:

* Users  
* Courses  
* Lessons  
* Assessments  
* Learning records

Admin endpoints should be protected with role-based access control. Optionally, participants may integrate a third-party admin tool such as SQLAdmin or Sqladmin for a web-based interface.

7. ### **Testing**

Participants must implement automated tests to ensure application reliability.

Testing should include:

* Unit tests for core logic (services, utilities)  
* API tests for critical endpoints using httpx.AsyncClient or TestClient  
* Validation of authentication and permissions

Testing should be done using pytest along with pytest-asyncio for async test support and HTTPX for API testing.

8. **Documentation**

Participants must provide documentation for the project, including:

* Project overview  
* Setup instructions  
* Environment configuration  
* Instructions for running the application  
* API documentation (FastAPI auto-generates interactive docs via Swagger UI and ReDoc)

[image1]: <data:image/png;base64,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>