"""Spans do fluxo principal, sem coletar dados pessoais."""
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.models.schemas import JobInput
from app.seed import initial_profile
from app.services import document_exporter, llm_provider, pipeline

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))


@pytest.fixture()
def spans(monkeypatch):
    # O provider global só pode ser definido uma vez; o tracer do app aponta para este provider nos testes.
    monkeypatch.setattr("app.telemetry.tracer", _provider.get_tracer("test"))
    for mod in (pipeline, document_exporter, llm_provider):
        monkeypatch.setattr(mod, "tracer", _provider.get_tracer("test"))
    _exporter.clear()
    return _exporter


def test_pipeline_emits_spans_without_personal_data(spans, job_text):
    p = initial_profile()
    a = pipeline.analyze_job(JobInput(job_description=job_text), p)
    r, _ = pipeline.build_resume(a, p)
    document_exporter.export_pdf(r)
    names = {s.name for s in spans.get_finished_spans()}
    assert {"pipeline.analyze_job", "job.parse_rules", "job.match", "pipeline.build_resume", "resume.generate_rules", "export.pdf"} <= names
    dump = " ".join(str(dict(s.attributes or {})) for s in spans.get_finished_spans())
    assert job_text[:30] not in dump and "christian@milfont.org" not in dump and "Christian" not in dump
    pdf = next(s for s in spans.get_finished_spans() if s.name == "export.pdf")
    assert pdf.attributes["export.pages"] == 1


def test_llm_span_records_metadata_and_errors(spans, monkeypatch, job_text):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "modelo-x")
    monkeypatch.setenv("LLM_API_KEY", "segredo")

    def boom(*a, **k):
        raise llm_provider.LLMError("falha simulada")

    monkeypatch.setattr(llm_provider, "_complete_json", boom)
    a = pipeline.analyze_job(JobInput(job_description=job_text), initial_profile())
    assert a.mode == "rules"
    finished = spans.get_finished_spans()
    req = next(s for s in finished if s.name == "llm.request")
    assert req.attributes["llm.model"] == "modelo-x" and req.status.status_code.name == "ERROR"
    assert "segredo" not in str(dict(req.attributes))
    root = next(s for s in finished if s.name == "pipeline.analyze_job")
    assert any(e.name == "llm.fallback" for e in root.events)
