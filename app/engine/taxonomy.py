"""Curated skill taxonomy.

Each canonical skill maps to the aliases that should count as a mention of it. Matching is
case-insensitive and boundary-aware, so "Java" does not match inside "JavaScript" and
"C" does not match inside "CSS".
"""

from __future__ import annotations

SKILLS: dict[str, dict[str, list[str]]] = {
    "languages": {
        "java": ["java", "java 8", "java 11", "java 17", "java 21", "core java"],
        "python": ["python", "python3", "py"],
        "javascript": ["javascript", "js", "ecmascript", "es6"],
        "typescript": ["typescript", "ts"],
        "c++": ["c++", "cpp"],
        "c#": ["c#", "csharp"],
        "go": ["go", "golang", "go lang"],
        "kotlin": ["kotlin"],
        "scala": ["scala"],
        "rust": ["rust"],
        "ruby": ["ruby"],
        "php": ["php"],
        "sql": ["sql", "t-sql", "pl/sql", "plsql"],
        "bash": ["bash", "shell scripting", "shell script"],
        "r": ["r programming", "r language"],
        "html": ["html", "html5"],
        "css": ["css", "css3", "scss", "sass"],
    },
    "backend": {
        "spring boot": ["spring boot", "springboot"],
        "spring": ["spring framework", "spring mvc", "spring"],
        "spring security": ["spring security"],
        "hibernate": ["hibernate", "jpa", "spring data jpa"],
        "microservices": ["microservices", "microservice", "micro-services"],
        "rest api": ["rest api", "rest apis", "restful", "restful api", "restful services", "rest"],
        "graphql": ["graphql"],
        "grpc": ["grpc"],
        "node.js": ["node.js", "nodejs", "node"],
        "express": ["express.js", "expressjs", "express"],
        "django": ["django"],
        "flask": ["flask"],
        "fastapi": ["fastapi"],
        ".net": [".net", "dotnet", "asp.net", ".net core"],
        "kafka": ["kafka", "apache kafka"],
        "rabbitmq": ["rabbitmq"],
        "maven": ["maven"],
        "gradle": ["gradle"],
        "junit": ["junit", "junit5"],
        "mockito": ["mockito"],
        "oauth": ["oauth", "oauth2", "openid connect", "oidc"],
        "jwt": ["jwt", "json web token", "json web tokens"],
    },
    "frontend": {
        "react": ["react", "react.js", "reactjs"],
        "angular": ["angular", "angularjs"],
        "vue": ["vue", "vue.js", "vuejs"],
        "redux": ["redux"],
        "next.js": ["next.js", "nextjs"],
        "tailwind": ["tailwind", "tailwindcss"],
        "webpack": ["webpack", "vite"],
    },
    "data": {
        "postgresql": ["postgresql", "postgres", "psql"],
        "mysql": ["mysql"],
        "oracle": ["oracle db", "oracle database", "oracle"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
        "cassandra": ["cassandra"],
        "dynamodb": ["dynamodb"],
        "pandas": ["pandas"],
        "numpy": ["numpy"],
        "spark": ["spark", "pyspark", "apache spark"],
        "airflow": ["airflow"],
        "etl": ["etl", "data pipelines", "data pipeline"],
        "data modeling": ["data modeling", "data modelling"],
    },
    "ml_ai": {
        "machine learning": ["machine learning", "ml"],
        "deep learning": ["deep learning"],
        "scikit-learn": ["scikit-learn", "sklearn"],
        "tensorflow": ["tensorflow", "keras"],
        "pytorch": ["pytorch", "torch"],
        "nlp": ["nlp", "natural language processing"],
        "llm": ["llm", "llms", "large language models", "large language model", "generative ai", "genai"],
        "computer vision": ["computer vision", "opencv"],
    },
    "cloud_devops": {
        "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
        "azure": ["azure", "microsoft azure"],
        "gcp": ["gcp", "google cloud", "google cloud platform"],
        "docker": ["docker", "containers", "containerization"],
        "kubernetes": ["kubernetes", "k8s", "eks", "aks", "gke"],
        "terraform": ["terraform"],
        "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous delivery", "continuous deployment"],
        "jenkins": ["jenkins"],
        "github actions": ["github actions"],
        "linux": ["linux", "unix"],
        "git": ["git", "github", "gitlab", "bitbucket"],
        "monitoring": ["prometheus", "grafana", "datadog", "splunk", "new relic"],
    },
    "practices": {
        "agile": ["agile", "scrum", "kanban"],
        "tdd": ["tdd", "test-driven development", "test driven development"],
        "unit testing": ["unit testing", "unit tests", "integration testing"],
        "system design": ["system design", "distributed systems", "scalability"],
        "data structures": ["data structures", "algorithms", "data structures and algorithms"],
        "design patterns": ["design patterns", "solid principles", "solid"],
        "security": ["owasp", "application security", "secure coding"],
    },
}

# Some short aliases are also common English words ("go", "rest", "node", "solid", "express", "r").
# They only count when the surrounding text looks technical, enforced in skills.py.
AMBIGUOUS_ALIASES = {
    "go", "rest", "node", "express", "solid", "spring", "oracle", "py", "ts", "ml", "torch", "r", "lambda",
}

SKILL_CATEGORY: dict[str, str] = {
    skill: category for category, skills in SKILLS.items() for skill in skills
}

ALIAS_TO_SKILL: dict[str, str] = {
    alias.lower(): skill for skills in SKILLS.values() for skill, aliases in skills.items() for alias in aliases
}
