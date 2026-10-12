"""Catálogo de termos técnicos: nome canônico -> (área, aliases). Usado para vaga e perfil."""
from __future__ import annotations

import re
from functools import lru_cache

# canônico: (área, [aliases em minúsculas])
CATALOG: dict[str, tuple[str, list[str]]] = {
    # Cloud / infra
    "AWS": ("cloud", ["aws", "amazon web services"]),
    "Azure": ("cloud", ["azure", "microsoft azure"]),
    "GCP": ("cloud", ["gcp", "google cloud", "google cloud platform"]),
    "Docker": ("cloud", ["docker", "containers", "contêineres", "conteineres", "containerização"]),
    "Kubernetes": ("cloud", ["kubernetes", "k8s"]),
    "EKS": ("cloud", ["eks", "amazon eks"]),
    "Terraform": ("cloud", ["terraform"]),
    "Ansible": ("cloud", ["ansible"]),
    "Helm": ("cloud", ["helm"]),
    "Linux": ("cloud", ["linux"]),
    "Infraestrutura como código": ("cloud", ["infraestrutura como código", "infraestrutura como codigo", "iac", "infrastructure as code"]),
    "Arquitetura cloud": ("cloud", ["arquitetura cloud", "arquitetura em nuvem", "cloud computing", "computação em nuvem", "cloud native"]),
    "Lambda": ("cloud", ["lambda", "serverless"]),
    "S3": ("cloud", ["s3"]),
    "EC2": ("cloud", ["ec2"]),
    "IAM": ("security", ["iam", "controle de acesso", "irsa"]),
    # DevOps
    "CI/CD": ("devops", ["ci/cd", "ci cd", "cicd", "integração contínua", "entrega contínua", "continuous integration", "continuous delivery", "pipelines"]),
    "Git": ("devops", ["git"]),
    "GitHub Actions": ("devops", ["github actions"]),
    "GitLab CI": ("devops", ["gitlab ci", "gitlab-ci", "gitlab"]),
    "Jenkins": ("devops", ["jenkins"]),
    "Argo CD": ("devops", ["argo cd", "argocd", "gitops"]),
    "Blue-green": ("devops", ["blue-green", "blue green"]),
    "Canary": ("devops", ["canary"]),
    "DevOps": ("devops", ["devops"]),
    "DevSecOps": ("security", ["devsecops"]),
    "Checkov": ("security", ["checkov"]),
    "FinOps": ("devops", ["finops"]),
    "Métricas DORA": ("devops", ["dora"]),
    "SRE": ("devops", ["sre", "site reliability"]),
    # Observabilidade
    "Observabilidade": ("observability", ["observabilidade", "observability"]),
    "Monitoramento": ("observability", ["monitoramento", "monitoring"]),
    "OpenTelemetry": ("observability", ["opentelemetry", "otel"]),
    "Grafana": ("observability", ["grafana"]),
    "Jaeger": ("observability", ["jaeger"]),
    "Dynatrace": ("observability", ["dynatrace"]),
    "Prometheus": ("observability", ["prometheus"]),
    "Datadog": ("observability", ["datadog"]),
    "New Relic": ("observability", ["new relic", "newrelic"]),
    "Splunk": ("observability", ["splunk"]),
    "ELK": ("observability", ["elk", "elasticsearch", "kibana"]),
    # Desenvolvimento
    "Python": ("backend", ["python"]),
    "Java": ("backend", ["java"]),
    "C#": ("backend", ["c#", "csharp"]),
    ".NET": ("backend", [".net", "dotnet", "asp.net"]),
    "Spring Boot": ("backend", ["spring boot", "spring"]),
    "FastAPI": ("backend", ["fastapi"]),
    "Django": ("backend", ["django"]),
    "Node.js": ("backend", ["node.js", "nodejs", "node js"]),
    "Go": ("backend", ["golang"]),
    "PHP": ("backend", ["php"]),
    "Ruby": ("backend", ["ruby"]),
    "Kotlin": ("backend", ["kotlin"]),
    "TypeScript": ("frontend", ["typescript"]),
    "JavaScript": ("frontend", ["javascript"]),
    "React": ("frontend", ["react", "reactjs", "react.js"]),
    "Angular": ("frontend", ["angular"]),
    "Vue": ("frontend", ["vue", "vue.js"]),
    "APIs REST": ("backend", ["api rest", "apis rest", "restful", "rest api", "rest apis", "apis", "api"]),
    "GraphQL": ("backend", ["graphql"]),
    "Microsserviços": ("backend", ["microsserviços", "microsservicos", "microserviços", "microservicos", "microservices", "microserviço"]),
    "Orientação a objetos": ("backend", ["orientação a objetos", "orientacao a objetos", "poo", "oop"]),
    "Testes automatizados": ("backend", ["testes automatizados", "tdd", "testes unitários", "testes unitarios", "unit tests"]),
    # Dados
    "SQL": ("data", ["sql"]),
    "Bancos relacionais": ("data", ["bancos de dados relacionais", "banco de dados relacional", "bancos relacionais", "rdbms"]),
    "PostgreSQL": ("data", ["postgresql", "postgres"]),
    "MySQL": ("data", ["mysql"]),
    "SQL Server": ("data", ["sql server", "sqlserver"]),
    "Oracle": ("data", ["oracle"]),
    "MongoDB": ("data", ["mongodb", "mongo"]),
    "Redis": ("data", ["redis"]),
    "DynamoDB": ("data", ["dynamodb"]),
    "Kafka": ("data", ["kafka"]),
    "RabbitMQ": ("data", ["rabbitmq"]),
    "SQS": ("data", ["sqs", "sns"]),
    "Mensageria": ("data", ["mensageria", "filas de mensagens", "fila de mensagens", "message queue", "message broker", "processamento assíncrono", "processamento assincrono"]),
    "Arquitetura orientada a eventos": ("data", ["orientada a eventos", "event-driven", "event driven"]),
    "Data lake": ("data", ["data lake", "data lakes"]),
    "Data warehouse": ("data", ["data warehouse", "data warehouses", "dw"]),
    "Engenharia de dados": ("data", ["engenharia de dados", "data engineering"]),
    "ETL": ("data", ["etl", "elt"]),
    "Spark": ("data", ["spark", "pyspark"]),
    "Airflow": ("data", ["airflow"]),
    "Power BI": ("data", ["power bi", "powerbi"]),
    # IA
    "IA generativa": ("ai", ["ia generativa", "generative ai", "genai", "gen ai", "ai generativa", "inteligência artificial generativa"]),
    "LLM": ("ai", ["llm", "llms", "large language model"]),
    "RAG": ("ai", ["rag", "retrieval augmented generation", "retrieval-augmented"]),
    "MCP": ("ai", ["mcp", "model context protocol"]),
    "Agentes de IA": ("ai", ["agentes de ia", "ai agents", "agentes de inteligência artificial"]),
    "Machine Learning": ("ai", ["machine learning", "aprendizado de máquina", "ml"]),
    "Inteligência artificial": ("ai", ["inteligência artificial", "inteligencia artificial"]),
    # Outros
    "Mobile": ("mobile", ["mobile", "react native", "expo", "flutter"]),
    "Metodologias ágeis": ("process", ["scrum", "kanban", "metodologias ágeis", "metodologias ageis", "agile", "ágil"]),
}

# Quando a vaga pede A e o perfil só tem B, conta como conhecimento relacionado (parcial).
RELATED: dict[str, list[str]] = {
    "Kafka": ["Mensageria", "SQS"],
    "RabbitMQ": ["Mensageria", "SQS"],
    "Mensageria": ["SQS"],
    "Jenkins": ["CI/CD", "GitHub Actions"],
    "GitLab CI": ["CI/CD", "GitHub Actions"],
    "Argo CD": ["CI/CD", "Kubernetes"],
    "Prometheus": ["Grafana", "Observabilidade"],
    "Datadog": ["Observabilidade", "Dynatrace"],
    "New Relic": ["Observabilidade", "Dynatrace"],
    "Splunk": ["Observabilidade"],
    "ELK": ["Observabilidade"],
    "SQL Server": ["SQL", "Bancos relacionais"],
    "Oracle": ["SQL", "Bancos relacionais"],
    "PostgreSQL": ["SQL", "MySQL"],
    "MongoDB": ["DynamoDB", "Bancos relacionais"],
    "Ansible": ["Terraform", "Infraestrutura como código"],
    "Helm": ["Kubernetes"],
    "Lambda": ["AWS"],
    "EC2": ["AWS"],
    "Spring Boot": ["Java"],
    "FastAPI": ["Python"],
    "Django": ["Python"],
    "Node.js": ["Python"],
    "LLM": ["IA generativa"],
    "Inteligência artificial": ["IA generativa", "LLM", "RAG", "Agentes de IA"],
    "Machine Learning": ["Inteligência artificial"],
    "Spark": ["Engenharia de dados"],
    "Airflow": ["Engenharia de dados"],
    "ETL": ["Engenharia de dados"],
}

SOFT_SKILLS = {
    "Comunicação": ["comunicação", "comunicacao", "comunicativ"],
    "Trabalho em equipe": ["trabalho em equipe", "colaboração", "colaboracao", "team player"],
    "Proatividade": ["proatividade", "proativ"],
    "Resolução de problemas": ["resolução de problemas", "resolucao de problemas", "problem solving", "solução de problemas"],
    "Autonomia": ["autonomia", "autônom", "autonom"],
    "Organização": ["organização", "organizacao"],
    "Liderança": ["liderança", "lideranca", "leadership"],
    "Aprendizado contínuo": ["aprendizado contínuo", "aprender", "curiosidade", "vontade de aprender"],
    "Pensamento analítico": ["analítico", "analitico", "raciocínio lógico", "raciocinio logico"],
    "Adaptabilidade": ["adaptabilidade", "flexibilidade", "adaptável"],
}


@lru_cache(maxsize=None)
def _pattern(alias: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", re.IGNORECASE)


def find_terms(text: str) -> list[str]:
    """Termos canônicos presentes no texto, na ordem de primeira aparição."""
    found: list[tuple[int, str]] = []
    for canon, (_area, aliases) in CATALOG.items():
        best = None
        for alias in aliases:
            m = _pattern(alias).search(text)
            if m and (best is None or m.start() < best):
                best = m.start()
        if best is not None:
            found.append((best, canon))
    found.sort()
    return [c for _, c in found]


def area_of(term: str) -> str:
    return CATALOG.get(term, ("other", []))[0]


def display_name(term: str) -> str:
    return {"EKS": "Amazon EKS", "Azure": "Microsoft Azure", "GCP": "Google Cloud Platform (GCP)"}.get(term, term)


_DISPLAY_REVERSE = {"Amazon EKS": "EKS", "Microsoft Azure": "Azure", "Google Cloud Platform (GCP)": "GCP"}


def canonical(name: str) -> str:
    """Inverso de display_name; devolve o próprio nome se já for canônico."""
    return _DISPLAY_REVERSE.get(name, name)
