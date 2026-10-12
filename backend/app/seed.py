"""Perfil inicial. Só contém dados fornecidos pelo usuário; campos não confirmados ficam vazios."""
from app.models.schemas import Profile


def initial_profile() -> Profile:
    return Profile.model_validate(
        {
            "personal": {
                # Nome inferido do handle do LinkedIn/GitHub; confirme e edite no perfil.
                "full_name": "Christian Milfont",
                "email": "christian@milfont.org",
                "phone": "+55 85 98191-3769",
                "location": "",
                "linkedin": "https://linkedin.com/in/christianmilfont",
                "github": "https://github.com/christianmilfont",
                "portfolio": "https://christianmilfont.github.io/code-cloud-portifolio/",
            },
            "education": [
                {
                    "course": "Graduação em Análise e Desenvolvimento de Sistemas (ADS)",
                    "institution": "FIAP",
                    "period": "Concluída em janeiro de 2026",
                    "status": "Concluída",
                },
                {
                    "course": "Pós-graduação em DevOps & Arquitetura Cloud",
                    "institution": "FIAP",
                    "period": "Em andamento",
                    "status": "Em andamento",
                },
            ],
            "achievements": [
                "Campeão do Pós Tech FIAP em DevOps e Arquitetura Cloud, com Shape da FIAP (avaliação de 60 questões).",
            ],
            "certifications": [
                {"name": "Google Cloud Generative AI Leader", "issuer": "Google Cloud"},
                {"name": "Microsoft Azure AZ-104", "issuer": "Microsoft"},
                {"name": "AWS re/Start", "issuer": "AWS"},
                {"name": "Dynatrace Essentials", "issuer": "Dynatrace"},
            ],
            "skills": [
                {
                    "name": "Cloud e infraestrutura",
                    "items": [
                        "AWS", "Microsoft Azure", "Google Cloud Platform (GCP)", "Docker", "Kubernetes",
                        "Amazon EKS", "Terraform", "Linux", "Infraestrutura como código", "Arquitetura cloud",
                    ],
                },
                {
                    "name": "DevOps e DevSecOps",
                    "items": [
                        "CI/CD", "Git", "GitHub Actions", "Deploy blue-green", "Deploy canary",
                        "Segurança de infraestrutura como código", "Checkov", "Controle de acesso (IAM)",
                        "FinOps", "Monitoramento", "Observabilidade", "Métricas DORA", "Práticas SRE",
                    ],
                },
                {
                    "name": "Desenvolvimento",
                    "items": [
                        "Python", "Java", "C#", ".NET", "APIs REST", "Microsserviços",
                        "Orientação a objetos", "Bancos de dados relacionais", "SQL", "PostgreSQL",
                        "MySQL", "Redis", "DynamoDB",
                    ],
                },
                {
                    "name": "Observabilidade e dados",
                    "items": [
                        "OpenTelemetry", "Grafana", "Jaeger", "Dynatrace", "Processamento assíncrono",
                        "Filas de mensagens", "Arquitetura orientada a eventos", "Data lakes",
                        "Data warehouses", "Fundamentos de engenharia de dados",
                    ],
                },
                {
                    "name": "Inteligência artificial",
                    "items": [
                        "IA generativa", "RAG", "MCP", "Integração de modelos de IA", "Agentes de IA",
                    ],
                },
            ],
            "projects": [
                {
                    "name": "ToggleMaster",
                    "subtitle": "Projeto de portfólio FIAP, DevOps e Arquitetura Cloud",
                    "description": (
                        "Arquitetura baseada em microsserviços e infraestrutura cloud, com foco em automação, "
                        "observabilidade, segurança, escalabilidade e eficiência operacional, aplicando práticas de "
                        "engenharia de software e DevOps em ambientes Kubernetes e AWS."
                    ),
                    "technologies": [
                        "AWS", "Amazon EKS", "Kubernetes", "Terraform", "Docker", "GitHub Actions", "Argo CD",
                        "OpenTelemetry", "Grafana", "Jaeger", "Datadog", "Checkov", "IAM", "IRSA", "Amazon S3",
                        "DynamoDB", "Redis", "PostgreSQL", "SQS", "FinOps",
                    ],
                    "bullets": [
                        "Observabilidade: OpenTelemetry, Grafana, Jaeger e Datadog em instrumentação, rastreamento distribuído e investigação de falhas (métricas, logs e traces).",
                        "Kubernetes: uso do Amazon EKS para implantar workloads conteinerizados, com deploy progressivo, rollback e disponibilidade.",
                        "CI/CD e GitOps: pipelines com GitHub Actions, estratégias blue-green e canary e estudos de integração com Argo CD.",
                        "Infraestrutura como código: provisionamento com Terraform, com foco em reprodutibilidade, versionamento e automação.",
                        "Segurança e DevSecOps: análise estática de IaC com Checkov, permissões com IAM e IRSA e proteção de configurações sensíveis.",
                        "Redes e arquitetura cloud: estruturação de VPC, sub-redes, roteamento e segmentação entre recursos públicos e privados.",
                        "Mensageria: Amazon SQS e Dead-Letter Queues (DLQ) na integração entre microsserviços e processamento orientado a eventos.",
                        "Persistência: S3, DynamoDB, Redis e PostgreSQL em diferentes contextos de armazenamento e acesso a dados.",
                        "Testes e confiabilidade: estratégias de validação de aplicações, infraestrutura e pipelines para prevenir regressões.",
                        "FinOps: decisões de arquitetura considerando custos, dimensionamento de recursos e equilíbrio entre desempenho e disponibilidade.",
                        "Monitoramento de infraestrutura: estudo da integração entre aplicações, serviços cloud e ferramentas de observabilidade.",
                    ],
                },
                {
                    "name": "SkillBridge",
                    "subtitle": "Plataforma de requalificação profissional",
                    "description": (
                        "Plataforma que conecta competências, cursos, microtarefas e oportunidades profissionais."
                    ),
                    "technologies": [
                        "ASP.NET Core 8", ".NET", "C#", "MySQL", "JWT", "OpenTelemetry",
                        "Azure Application Insights", "Expo", "APIs REST",
                    ],
                    "bullets": [
                        "API em ASP.NET Core 8 com persistência em MySQL e autenticação via JWT.",
                        "Instrumentação com OpenTelemetry e Azure Application Insights.",
                        "Aplicação mobile desenvolvida com Expo.",
                    ],
                },
                {
                    "name": "Projetos acadêmicos e de portfólio",
                    "subtitle": "",
                    "description": (
                        "Projetos acadêmicos e de portfólio envolvendo Java, Spring Boot, APIs, bancos de "
                        "dados, interfaces web e integração de inteligência artificial."
                    ),
                    "technologies": [
                        "Java", "Spring Boot", "APIs REST", "Bancos de dados relacionais", "SQL",
                        "Integração de modelos de IA",
                    ],
                    "bullets": [
                        "Desenvolvimento de APIs em Java com Spring Boot integradas a bancos de dados.",
                        "Interfaces web e integração de inteligência artificial em projetos de portfólio.",
                    ],
                },
            ],
            "experiences": [
                {
                    "company": "Produto Reativo",
                    "role": "Analista de Requisitos e Engenheiro de Software",
                    "start": "2024",
                    "end": "2025",
                    "location": "Remoto",
                    "bullets": [
                        "Levantamento e documentação de requisitos funcionais e não funcionais, traduzindo necessidades de negócio em especificações técnicas.",
                        "Desenvolvimento e evolução de aplicações, APIs e serviços, com boas práticas de engenharia de software e integração entre sistemas.",
                        "Uso de serviços AWS e Google Cloud Platform (GCP) em arquitetura, desenvolvimento e implementação de soluções em cloud.",
                        "Participação em decisões técnicas sobre arquitetura, estruturação de dados, integração de serviços e escalabilidade.",
                        "Aplicação de conceitos de DevOps, automação e integração contínua no ciclo de desenvolvimento e entrega.",
                        "Interface entre requisitos de negócio e implementação técnica, apoiando a validação e a qualidade das entregas.",
                    ],
                },
                {
                    "company": "Produto Reativo",
                    "role": "Coordenador de Projetos Digitais",
                    "start": "Janeiro de 2023",
                    "end": "Julho de 2024",
                    "location": "Híbrido",
                    "bullets": [
                        "Coordenação de projetos digitais em três contratos com clientes de SP, PE e CE, conectando equipes, requisitos e entregas técnicas.",
                        "Organização de prioridades, prazos e entregas com metodologias ágeis, alinhando stakeholders e promovendo melhoria contínua.",
                        "Levantamento e organização de requisitos, transformando necessidades de negócio em soluções digitais.",
                        "Facilitação da comunicação entre equipes e remoção de impedimentos no fluxo de trabalho.",
                        "Visitas presenciais aos clientes para coletar feedbacks e novos pedidos diretamente com eles.",
                    ],
                },
                {
                    "company": "Produto Reativo",
                    "role": "Agilista Aprendiz | Analista de Requisitos",
                    "start": "Janeiro de 2021",
                    "end": "Dezembro de 2022",
                    "location": "Remoto",
                    "bullets": [
                        "Desenvolvimento de plataforma de Marketing Digital para games na startup DX (investida pela We Ventures, administrada pela Bertha com a Microsoft).",
                        "Levantamento e documentação de requisitos funcionais e regras de negócio para orientar o desenvolvimento.",
                        "Tradução das necessidades dos stakeholders em funcionalidades e especificações técnicas com as equipes de desenvolvimento.",
                        "Apoio à organização do backlog, priorização de demandas e acompanhamento das entregas com práticas ágeis.",
                        "Refinamento de demandas e validação das funcionalidades conforme os requisitos definidos.",
                    ],
                },
            ],
            "languages": [],
        }
    )
