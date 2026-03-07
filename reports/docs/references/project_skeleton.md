Hybrid Agentic ML for Risk Assessment
├── LICENSE.txt                <- Project's license (MIT)
├── README.md                  <- The top-level README for developers using this project
├── .env                       <- Environment variables
├── .gitignore                 <- Files to ignore by Git
├── dvc.yaml                   <- The Pipeline Conductor
├── pyproject.toml             <- UV dependency definitions
├── main.py                    <- Pipeline Orchestrator (Script mode)
├── Dockerfile                 <- Production container definition
├── .dockerignore              <- Files to ignore by Docker
│
├── .github/
│   └── workflows/             <- CI/CD workflows
│
├── artifacts/                 <- Generated artifacts (models, metrics, transformed data, serialized models, etc.)
│
├── config/                    <- Centralize all configuration files ("source of truth")
│   ├── config.yaml            <- System paths (artifacts/data)
│   ├── params.yaml            <- Hyperparameters (K-neighbors, Chunk size)
│   └── schema.yaml            <- Data schema definitions
│
├── data/
│   ├── external               <- Data from third party sources
│   ├── processed              <- The final, canonical data sets for modeling
│   └── raw                    <- The original, immutable data dump
│
├── logs/                      <- Logs of the pipeline execution
│
├── notebooks/                 <- Jupyter notebooks (EDA, prototyping)
│
├── reports/                   <- Generated analysis, documentation, and visualizations for stakeholders
│   ├── docs/                  <- Generated documents to be used in reporting
│   │   ├── architecture/      <- System architecture diagrams and descriptions (The What)
│   │   ├── decisions/         <- Decisions made during the project (The Why)
│   │   ├── references/        <- Data dictionaries, manuals, and all other high-level explanatory materials
│   │   ├── runbooks/          <- Instructions for the project, what’s allowed / not allowed (The Rules)
│   │   └── workflows/         <- Technical implementation of the project (The How)
│   └── figures/               <- Generated graphics and figures to be used in reporting
│
├── tests/                     <- Unit, integration, app, and agentic tests
│
└── src/                            <- Source code for use in this project
    │
    ├── __init__.py                 <- Makes src a Python module
    │
    ├── agents/                     <- Agent code
    │   ├── __init__.py             <- Makes agents a Python module
    │   ├── tools/                  <- Tools for agents
    │   ├── config.py               <- Agent configuration
    │   ├── graph.py                <- Agent graph
    │   └── model_factory.py        <- Model factory for agents
    │
    ├── app/                        <- Application code
    │   ├── __init__.py             <- Makes app a Python module
    │   ├── api/                    <- API endpoints
    │   ├── main.py                 <- Application entry point
    │   └── schemas.py              <- Pydantic schemas for API
    │
    ├── components/                 <- Business Logic/Workers (The "How")
    │
    ├── config/                     <- Configuration Management ('Brain' of the system)
    │   └── configuration.py        <- Centralizes the orchestration of configurations and parameters
    │
    ├── entity/                     <- Data entities
    │   └── config_entity.py        <- Dataclass entity definitions
    │
    ├── features/                   <- Feature engineering
    │   └── build_features.py       <- Code to create features for modeling
    │
    ├── pipeline/                   <- Execution Stages (The "Conductor")
    │
    └── utils/                      <- Common tools
        ├── common.py               <- Config readers
        ├── exception.py            <- Custom Error Handling (Reliability)
        ├── logger.py               <- Logging configuration
        └── mlflow_config.py        <- MLflow configuration across modules
