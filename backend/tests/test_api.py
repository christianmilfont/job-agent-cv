"""Fluxo principal via API, incluindo persistência após 'reiniciar' (nova conexão ao mesmo arquivo)."""
from fastapi.testclient import TestClient


def test_status_reports_rules_mode(client):
    s = client.get("/api/status").json()
    assert s["ai_enabled"] is False and s["mode"] == "rules"


def test_profile_get_update_persist(client):
    p = client.get("/api/profile").json()
    assert p["personal"]["email"] == "christian@milfont.org"
    p["personal"]["email"] = "teste@example.com"
    p["languages"] = [{"name": "Inglês", "level": "Intermediário"}]
    assert client.put("/api/profile", json=p).status_code == 200
    again = client.get("/api/profile").json()
    assert again["personal"]["email"] == "teste@example.com" and again["languages"][0]["name"] == "Inglês"
    assert client.post("/api/profile/reset").json()["personal"]["email"] == "christian@milfont.org"


def test_full_flow_and_restart(client, job_text, tmp_path):
    r = client.post("/api/applications", json={"job_description": job_text})
    assert r.status_code == 201
    app = r.json()
    assert app["role"].startswith("Analista DevOps") and 0 <= app["score"] <= 100
    assert app["analysis"]["mode"] == "rules"
    assert app["resume"] == app["resume_generated"]

    edited = app["resume"]
    edited["summary"] = "Resumo editado manualmente."
    up = client.put(f"/api/applications/{app['id']}", json={"resume": edited, "company": "Acme"})
    assert up.status_code == 200 and up.json()["resume"]["summary"] == "Resumo editado manualmente."

    pdf = client.get(f"/api/applications/{app['id']}/export/pdf")
    docx = client.get(f"/api/applications/{app['id']}/export/docx")
    assert pdf.content.startswith(b"%PDF") and "attachment" in pdf.headers["content-disposition"]
    assert docx.content[:2] == b"PK"
    assert client.post("/api/export/pdf", json=edited).content.startswith(b"%PDF")

    # "reinicia": novo cliente apontando para o mesmo banco
    from app.main import app as fastapi_app

    with TestClient(fastapi_app) as c2:
        hist = c2.get("/api/applications").json()
        assert len(hist) == 1 and hist[0]["company"] == "Acme"
        reopened = c2.get(f"/api/applications/{app['id']}").json()
        assert reopened["resume"]["summary"] == "Resumo editado manualmente."
        assert reopened["job_description"] == job_text.strip()
        restored = c2.post(f"/api/applications/{app['id']}/restore").json()
        assert restored["resume"]["summary"] != "Resumo editado manualmente."

    assert client.delete(f"/api/applications/{app['id']}").status_code == 204
    assert client.get(f"/api/applications/{app['id']}").status_code == 404


def test_validation_and_errors(client):
    r = client.post("/api/applications", json={"job_description": "curto"})
    assert r.status_code == 422 and "muito curta" in r.json()["detail"]
    assert client.get("/api/applications/999").status_code == 404
    assert client.get("/api/applications/1/export/txt").status_code in (400, 404)
    assert client.post("/api/export/exe", json={}).status_code == 400
    assert client.post("/api/export/pdf", json={"section_order": ["inexistente"]}).status_code == 422


def test_analyze_and_generate_endpoints(client, job_text):
    a = client.post("/api/analyze", json={"job_description": job_text, "company": "Acme", "role": "SRE"})
    assert a.status_code == 200 and a.json()["job"]["company"] == "Acme"
    g = client.post("/api/resume/generate", json={"job_description": job_text})
    assert g.status_code == 200 and g.json()["name"]
    assert client.get("/api/applications").json() == []  # estes endpoints não salvam
