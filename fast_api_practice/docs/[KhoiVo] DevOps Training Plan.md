![][image1]  
www.agilityio.com

# DevOps Training Plan

## **April 06, 2026**

# **OVERVIEW**

This training plan provides a structured 3 days program to equip developers with practical Docker containerization skills and Railway cloud deployment expertise. Trainees will progress from foundational container concepts to deploying production-ready multi-service applications.

The program is designed around hands-on labs, with each session combining theory (30%) and practice (70%) to maximize retention and real-world applicability.

## **PREREQUISITES**

* Basic command-line / terminal proficiency (bash or PowerShell)  
* Fundamental understanding of web applications (HTTP, REST APIs, databases)  
* A GitHub account (for Railway integration)  
* Docker Desktop installed (Windows / macOS) or Docker Engine (Linux)  
* A Railway account (free trial available at railway.com)  
* Node.js 18+ or Python 3.10+ installed locally  
* Code editor (VS Code recommended)

## **OBJECTIVES**

By the end of this training, participants will be able to:

1\.     Explain Docker architecture (daemon, client, images, containers, registries)

2\.     Write efficient, multi-stage Dockerfiles following best practices

3\.     Build, tag, and push Docker images to registries

4\.     Manage container data with volumes and bind mounts

5\.     Orchestrate multi-container applications using Docker Compose

6\.     Configure and deploy services on Railway via GitHub integration and CLI

7\.     Manage environment variables, networking, and domains in Railway

8\.     Set up CI/CD pipelines for automatic deployment on push

9\.     Attach persistent storage and managed databases in Railway

10\.  Monitor deployments with logs, metrics, and health checks

# **TIMELINE**

**Total: 3 days (approx. 8 hours per day)**

**Schedule Summary**

| Day | Focus Area | Key Outcome |
| :---- | :---- | :---- |
| **Day 1** | Docker Fundamentals | Build & run containerized apps locally |
| **Day 2** | Docker Compose \+ Railway Basics | Multi-container apps deployed on Railway |
| **Day 3**  | Advanced Railway \+ Production | Production-ready CI/CD pipeline |

## **DAY 1 \- Docker Fundamentals**

| Topic | Details / Activities | Resources |
| :---- | :---- | :---- |
| **What is Docker?** | Docker architecture: daemon, client, REST API Containers vs. virtual machines Use cases: CI/CD, microservices, dev environments | [Docker Overview](https://docs.docker.com/get-started/docker-overview/) |
| **Images & Containers** | Image layers & union filesystem Pulling images from Docker Hub Running containers: run, start, stop, rm Inspecting: logs, exec, inspect | [What is a container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) [What is an image?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/) |
| **Writing Dockerfiles** | Instructions: FROM, RUN, COPY, WORKDIR, EXPOSE, CMD, ENTRYPOINT Build context and .dockerignore Lab: Containerize a Node.js or Python app | [Writing a Dockerfile](https://docs.docker.com/get-started/docker-concepts/building-images/writing-a-dockerfile/) |
| **Build & Tag Images** | docker build \-t, tagging conventions Understanding image layers and caching Lab: Build, tag, and inspect image layers | [Build, tag, publish](https://docs.docker.com/get-started/docker-concepts/building-images/build-tag-and-publish-an-image/) |
| **Multi-Stage Builds** | Reducing image size with multi-stage Build stage vs. runtime stage Lab: Refactor Dockerfile to multi-stage | [Multi-stage builds](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/) |
| **Data Persistence** | Volumes vs. bind mounts vs. tmpfs Creating and managing named volumes Lab: Persist database data across restarts | [Persisting data](https://docs.docker.com/get-started/docker-concepts/running-containers/persisting-container-data/) |
| **Networking & Ports** | Container networking basics (bridge, host) Publishing and exposing ports Container-to-container communication | [Publishing ports](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/) |
| **Registries & Sharing** | Docker Hub: push, pull, repositories Private registries overview Lab: Push your image to Docker Hub | [What is a registry?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-registry/) |

## 

## **DAY 2 \- Docker Compose \+ Railway Basics**

| Topic | Details / Activities | Resources |
| :---- | :---- | :---- |
| **Docker Compose** | YAML syntax for multi-container apps Defining services, networks, volumes docker compose up / down / logs Lab: Compose a web app \+ database stack | [What is Docker Compose?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-docker-compose/) |
| **Multi-Container Apps** | Service dependencies (depends\_on) Environment variables in Compose Health checks and restart policies Lab: Add Redis cache to your stack | [Multi-container apps](https://docs.docker.com/get-started/docker-concepts/running-containers/multi-container-applications/) |
| **Railway Introduction** | Platform overview and philosophy Core concepts: Projects, Services, Environments Dashboard walkthrough Railway vs. other PaaS | [Railway Docs](https://docs.railway.com/) [The Basics](https://docs.railway.com/overview/the-basics) |
| **Deploy to Railway** | Connecting a GitHub repo Auto-deploy on push Reviewing build & deploy logs Lab: Deploy your Dockerized app to Railway | [Quick Start](https://docs.railway.com/quick-start) |
| **Railway CLI** | Installing the CLI railway login, link, deploy Local dev with railway run Lab: Deploy via CLI | [CLI Reference](https://docs.railway.com/cli) |
| **Variables & Networking** | Service variables and shared variables Reference variables (${{service.VAR}}) Custom domains and HTTPS Private networking between services | [Variables](https://docs.railway.com/variables) |
| **Managed Databases** | Adding PostgreSQL / MySQL / Redis from templates Connecting services via variables Lab: Attach a PostgreSQL database to your app | [Databases Guide](https://docs.railway.com/guides/databases) |

## **DAY 3 \- Advanced Railway & Production Readiness**

| Topic | Details / Activities | Resources |
| :---- | :---- | :---- |
| **Dockerfile Best Practices** | Build cache optimization Security: non-root users, minimal base images .dockerignore strategies Lab: Optimize image from 1GB to \<200MB | [Build cache](https://docs.docker.com/get-started/docker-concepts/building-images/using-the-build-cache/) |
| **Config as Code** | railway.toml / railway.json configuration Build and deploy settings in code Nixpacks vs. custom Dockerfiles on Railway | [Config as Code](https://docs.railway.com/config-as-code) |
| **Environments & CI/CD** | Staging vs. production environments PR-based preview deployments GitHub Actions integration Lab: Set up staging → production pipeline | [Environments](https://docs.railway.com/environments) |
| **Volumes & Persistence** | Railway volumes: attach, mount, backup Use cases for persistent storage Storage bucket overview | [Volumes](https://docs.railway.com/volumes) [Storage Buckets](https://docs.railway.com/guides/storage-buckets) |
| **Monitoring & Logs** | Deploy logs and runtime logs Service metrics (CPU, memory, network) Health checks and alerts | [Monitoring](https://docs.railway.com/guides/monitoring) |
| **Scaling & Cost Control** | Horizontal and vertical scaling Understanding your bill Cost control strategies and usage limits | [Plans & Pricing](https://docs.railway.com/pricing/plans) [Cost Control](https://docs.railway.com/pricing/cost-control) |
| **Capstone Project** | Deploy a full-stack application:   • Frontend (React/Next.js)   • Backend API (Node/Python)   • PostgreSQL \+ Redis Dockerized locally, deployed on Railway | [Production Checklist](https://docs.railway.com/overview/production-readiness-checklist) |
| **Wrap-Up & Next Steps** | Production readiness checklist review Advanced topics: Kubernetes, Terraform Q\&A and feedback Certificate of completion | [Best Practices](https://docs.railway.com/overview/best-practices) |

# **KEY RESOURCES**

## **Docker**

•       [Docker Official Documentation](https://docs.docker.com/)

•       [Docker Get Started Guide](https://docs.docker.com/get-started/)

•       [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)

•       [Docker Compose Reference](https://docs.docker.com/compose/)

•       [Docker Hub](https://hub.docker.com/)

## **Railway**

•       [Railway Documentation](https://docs.railway.com/)

•       [Railway Quick Start](https://docs.railway.com/quick-start)

•       [Railway CLI Reference](https://docs.railway.com/cli)

•       [Railway Templates](https://railway.com/templates)

•       [Railway Changelog](https://railway.com/changelog)

[image1]: <data:image/png;base64,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>