from fastapi import APIRouter, HTTPException, Response

from app import database
from app.models.schemas import (
    Analysis, Application, ApplicationSummary, ApplicationUpdate, JobInput, ResumeContent,
)
from app.services import document_exporter, pipeline

router = APIRouter(prefix="/api", tags=["candidaturas"])

MEDIA = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _get_or_404(app_id: int) -> Application:
    app = database.get_application(app_id)
    if app is None:
        raise HTTPException(404, "Candidatura não encontrada.")
    return app


@router.post("/analyze", response_model=Analysis)
def analyze(data: JobInput) -> Analysis:
    """Analisa a vaga contra o perfil, sem salvar."""
    return pipeline.analyze_job(data, database.get_profile())


@router.post("/resume/generate", response_model=ResumeContent)
def generate(data: JobInput) -> ResumeContent:
    """Gera apenas o currículo (sem salvar)."""
    profile = database.get_profile()
    analysis = pipeline.analyze_job(data, profile)
    return pipeline.build_resume(analysis, profile)[0]


@router.post("/applications", response_model=Application, status_code=201)
def create_application(data: JobInput) -> Application:
    """Fluxo principal: analisa, gera o currículo e salva a candidatura."""
    profile = database.get_profile()
    analysis = pipeline.analyze_job(data, profile)
    resume, notices = pipeline.build_resume(analysis, profile)
    analysis.notices += notices
    return database.create_application(
        data.company or analysis.job.company, data.role or analysis.job.title, data.job_description, analysis, resume
    )


@router.get("/applications", response_model=list[ApplicationSummary])
def list_applications() -> list[ApplicationSummary]:
    return database.list_applications()


@router.get("/applications/{app_id}", response_model=Application)
def read_application(app_id: int) -> Application:
    return _get_or_404(app_id)


@router.put("/applications/{app_id}", response_model=Application)
def update_application(app_id: int, data: ApplicationUpdate) -> Application:
    _get_or_404(app_id)
    updated = database.update_application(app_id, data.company, data.role, data.resume)
    assert updated is not None
    return updated


@router.post("/applications/{app_id}/restore", response_model=Application)
def restore_generated(app_id: int) -> Application:
    """Descarta as edições e volta ao currículo originalmente gerado."""
    _get_or_404(app_id)
    restored = database.reset_application_resume(app_id)
    assert restored is not None
    return restored


@router.delete("/applications/{app_id}", status_code=204)
def delete_application(app_id: int) -> Response:
    if not database.delete_application(app_id):
        raise HTTPException(404, "Candidatura não encontrada.")
    return Response(status_code=204)


def _file_response(resume: ResumeContent, fmt: str) -> Response:
    try:
        content = document_exporter.export_pdf(resume) if fmt == "pdf" else document_exporter.export_docx(resume)
    except Exception as exc:  # erro de renderização não deve vazar detalhes internos
        raise HTTPException(500, "Não foi possível gerar o arquivo. Verifique o conteúdo do currículo.") from exc
    name = document_exporter.safe_filename(resume, fmt)
    return Response(content, media_type=MEDIA[fmt], headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/applications/{app_id}/export/{fmt}")
def export_saved(app_id: int, fmt: str) -> Response:
    if fmt not in MEDIA:
        raise HTTPException(400, "Formato inválido. Use pdf ou docx.")
    return _file_response(_get_or_404(app_id).resume, fmt)


@router.post("/export/{fmt}")
def export_content(fmt: str, resume: ResumeContent) -> Response:
    """Exporta o conteúdo enviado (ex.: edição ainda não salva)."""
    if fmt not in MEDIA:
        raise HTTPException(400, "Formato inválido. Use pdf ou docx.")
    return _file_response(resume, fmt)
