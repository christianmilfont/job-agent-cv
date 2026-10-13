"""Observabilidade com OpenTelemetry (traces via OTLP/HTTP para o Collector).

Desativada por padrão. Para ativar, defina OTEL_EXPORTER_OTLP_ENDPOINT (ex.: http://localhost:4318).
Privacidade: spans guardam apenas tamanhos, contagens, modo e nomes de modelo — nunca o texto da vaga,
dados do perfil ou conteúdo das respostas da IA.
"""
from __future__ import annotations

import logging
import os

from opentelemetry import trace

log = logging.getLogger("jobagent.telemetry")

# Sem SDK configurado, este tracer é um no-op (custo desprezível), então os serviços podem usá-lo sempre.
tracer = trace.get_tracer("jobagent-cv")

_configured = False


def setup(app=None) -> bool:
    """Configura SDK, exportador OTLP e instrumentação automática. Retorna True se ativou."""
    global _configured
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip().rstrip("/")
    if _configured or not endpoint or os.environ.get("OTEL_SDK_DISABLED", "").lower() == "true":
        if not endpoint:
            log.info("Telemetria desativada (OTEL_EXPORTER_OTLP_ENDPOINT não definido).")
        return _configured

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", "jobagent-cv-backend"),
        "service.version": "1.0.0",
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()  # chamadas ao provedor de IA (Ollama etc.)
    if app is not None:
        FastAPIInstrumentor.instrument_app(app, excluded_urls="api/status", exclude_spans=["receive", "send"])  # sem ruído do polling de status
    _configured = True
    log.info("Telemetria ativa: traces enviados para %s", endpoint)
    return True
