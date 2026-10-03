import pytest

RESUME = """Sri Ram Teja Ialam
ramtejasri65@gmail.com | (603) 932-0249 | github.com/si1051 | Manchester, NH

Summary
Full stack engineer building Java and Python services.

Experience
Software Engineer, Acme Corp | Jan 2021 - Present
- Built Spring Boot microservices on AWS serving 2M requests/day using Kafka and PostgreSQL
- Reduced API latency by 40% by introducing Redis caching and query tuning
- Automated CI/CD with GitHub Actions and Docker, cutting release time from 2 hours to 15 minutes
- Responsible for various tasks
Software Engineering Intern, Globex | May 2019 - Aug 2020
- Developed React dashboards used by 300 internal analysts

Education
M.S. Computer Science, University of New Hampshire, 2024

Skills
Java, Python, Spring Boot, React, PostgreSQL, Docker, Git, REST APIs, JUnit
"""

JOB = """About the role
Join our platform team building payment services.

Requirements:
- 3+ years of professional experience with Java and Spring Boot
- Experience designing REST APIs and microservices
- Hands-on with Kubernetes and PostgreSQL
- Strong testing habits (JUnit)

Nice to have:
- Kafka, Terraform
- Experience with observability tooling

Benefits
- Health insurance and 401k
"""


@pytest.fixture
def resume():
    return RESUME


@pytest.fixture
def job():
    return JOB
