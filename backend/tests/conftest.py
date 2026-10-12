import os

import pytest

JOB = """Analista DevOps Pleno - Acme Tecnologia

Responsabilidades:
- Construir pipelines CI/CD com GitHub Actions
- Gerenciar clusters Kubernetes na AWS usando Terraform
- Implementar observabilidade com Prometheus e Grafana

Requisitos:
- 3 anos de experiência com DevOps
- Docker, Kubernetes, AWS, Terraform
- Inglês avançado
- Graduação em Tecnologia da Informação

Diferenciais:
- Conhecimento em Kafka
- Certificação AWS
"""


@pytest.fixture(autouse=True)
def _no_llm_from_env(monkeypatch):
    import app.main  # noqa: F401  (carrega o .env uma vez, antes de limpar as variáveis)

    """O .env do usuário pode ativar a IA; os testes nunca devem chamar um provedor real."""
    for k in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(k, raising=False)


@pytest.fixture()
def job_text():
    return JOB


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBAGENT_DB", str(tmp_path / "test.db"))
    for k in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
