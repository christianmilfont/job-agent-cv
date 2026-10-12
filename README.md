# Job Agent CV

Gera currículos personalizados para cada vaga a partir de um perfil profissional persistente.
Cole a vaga → veja análise de compatibilidade (MATCH / GAPS / RISKS) → edite o currículo → baixe PDF ou DOCX.

- **Frontend:** React + Vite + TypeScript (CSS convencional)
- **Backend:** Python + FastAPI + Pydantic + SQLite (arquivo local)
- **Documentos:** `reportlab` (PDF com texto selecionável e links clicáveis) e `python-docx` (DOCX)
- **IA:** opcional. Sem configuração, tudo funciona em **modo por regras/templates**, e a interface avisa isso.

Seus dados ficam apenas em `backend/data/jobagent.db` (ignorado pelo Git). Nada é enviado a terceiros, exceto se você configurar um provedor de IA (aí o texto da vaga e os fatos do seu perfil vão para esse provedor).

## Requisitos

- Python 3.11+ e Node.js 18+

## Instalação

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell/cmd)   |   source .venv/bin/activate  (Linux/macOS)
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## Execução

**Desenvolvimento (dois terminais):**

```bash
# terminal 1 — API em http://127.0.0.1:8000
cd backend && uvicorn app.main:app --reload

# terminal 2 — interface em http://localhost:5173
cd frontend && npm run dev
```

**Uso local com um único servidor:** rode `npm run build` em `frontend/` e depois só o backend;
a interface fica em http://127.0.0.1:8000.

## Como usar

1. **Perfil** — botão *Editar perfil profissional*. Já vem preenchido com os dados fornecidos (formação, certificações, competências, projetos, links). Preencha e-mail, telefone, cidade, idiomas e experiências reais quando quiser; o que estiver vazio não aparece no currículo. Também dá para editar tudo via `PUT /api/profile`; o perfil inicial está em `backend/app/seed.py`.
2. **Gerar** — cole a vaga na tela inicial (empresa/cargo opcionais) e clique em *Analisar vaga e gerar currículo*.
3. **Resultado** — abas *Visão geral* (score e como foi calculado), *Requisitos* (MATCH/GAPS/RISKS), *Currículo* (editor + pré-visualização, ordem das seções) e *Exportar*.
4. **Baixar** — *Baixar PDF* / *Baixar DOCX* (a aba também tem pré-visualização do PDF real). Alterações pendentes são salvas antes de exportar.
5. **Histórico** — a tela inicial lista todas as candidaturas; abra qualquer uma para continuar editando.

## Configurar a IA (opcional)

Copie `.env.example` para `.env` na raiz e preencha:

```ini
# OpenAI ou qualquer API compatível (OpenRouter, Groq...)
LLM_PROVIDER=openai
LLM_API_KEY=sua-chave
LLM_MODEL=nome-do-modelo

# Anthropic
LLM_PROVIDER=anthropic
LLM_API_KEY=sua-chave
LLM_MODEL=nome-do-modelo

# Local e gratuito com Ollama (sem chave)
LLM_PROVIDER=openai
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1
```

Reinicie o backend. Com IA ativa:
- a extração da vaga é refinada pela IA (termos que não aparecem literalmente na vaga são descartados);
- **título e resumo** do currículo são redigidos pela IA usando só os fatos do perfil, e o texto é **validado** — é rejeitado se citar tecnologias sem respaldo no perfil, números/métricas, anos de experiência ou atuação profissional não cadastrada;
- em qualquer falha (rede, chave, resposta inválida, validação) o sistema volta ao modo por regras e mostra um aviso na candidatura.

Competências, projetos, formação, certificações e o restante do currículo sempre vêm do perfil, nunca da IA.

## Como o modo sem IA funciona (e seus limites)

- Reconhece ~100 tecnologias/termos de um catálogo fixo (`backend/app/services/catalog.py`, com sinônimos). Tecnologias fora dele não são detectadas.
- Separa seções da vaga por títulos (Requisitos, Diferenciais…). Vagas sem estrutura têm todos os termos tratados como obrigatórios.
- O resumo vem de um modelo de texto; é correto e honesto, mas menos "natural" que o gerado por IA.
- **Score:** tecnologias obrigatórias (40) + desejáveis (10) + formação/certificações (15) + projetos (15) + experiência (20), normalizado para 0–100. Conhecimento *relacionado* (ex.: Grafana para Prometheus) dá crédito parcial e é sinalizado em GAPS. Lacuna = "não encontrado no perfil", não "não sabe". O score é uma estimativa e **não garante aprovação em ATS**.

## Testes

```bash
cd backend
pytest -q
```

Cobrem parsing, score, integridade do perfil (sem dados inventados), geração (só termos com respaldo), camada de IA (inclusive fallback e validação anti-invenção), exportação PDF/DOCX (texto extraível, links, ordem das seções) e o fluxo completo da API com persistência. Para o frontend: `npm run build` executa a checagem de tipos.

## Estrutura

```
backend/app/main.py                  inicialização da API (e serve frontend/dist se existir)
backend/app/models/schemas.py        schemas Pydantic
backend/app/seed.py                  perfil inicial
backend/app/database.py              SQLite (perfil + candidaturas)
backend/app/routers/                 rotas /api/profile, /api/analyze, /api/applications, /api/export...
backend/app/services/job_parser.py   extração de requisitos
backend/app/services/job_matcher.py  score e MATCH/GAPS/RISKS
backend/app/services/resume_generator.py  seleção e ordenação do conteúdo
backend/app/services/llm_provider.py integração opcional com IA + validação
backend/app/services/document_exporter.py PDF e DOCX
backend/tests/                       testes
frontend/src/                        interface React
```
