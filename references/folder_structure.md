Project-Name
├── LICENSE.txt                <- Project's license (Open-source if one is chosen)
├── README.md                  <- The top-level README for developers using this project
├── .env                       <- Environment variables
├── .gitignore                 <- Files to ignore by Git
├── dvc.yaml                   <- The Pipeline Conductor
├── pyproject.toml             <- UV dependency definitions
├── main.py                    <- Pipeline Orchestrator (Script mode)
├── Dockerfile                 <- Production container definition
│
├── config/                    <- Configuration files
│   ├── config.yaml            <- System paths (artifacts/data)
│   └── params.yaml            <- Hyperparameters (K-neighbors, Chunk size)
│
├── artifacts/                 <- Generated artifacts
│
├── .github/
│   └── workflows/             <- CI/CD (main.yaml)
│
├── config/
│   ├── config.yaml            <- System paths (artifacts/data)
│   └── params.yaml            <- Hyperparameters (K-neighbors, Chunk size)
│
├── data/
│   ├── external               <- Data from third party sources
│   ├── interim                <- Intermediate data that has been transformed
│   ├── processed              <- The final, canonical data sets for modeling
│   └── raw                    <- The original, immutable data dump
│
├── logs/                      <- Logs of the pipeline execution
│
├── models/                    <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks/                 <- Jupyter notebooks
│
├── references/                <- Data dictionaries, manuals, and all other explanatory materials
│   └── folder_structure.md
│
├── reports/                   <- Generated analysis as HTML, PDF, LaTeX, etc.
│   ├── docs/                  <- Generated documents to be used in reporting
│   └── figures/               <- Generated graphics and figures to be used in reporting
│
├── tests/                     <- Unit tests and integration tests
│
└── src/                            <- Source code for use in this project
    │
    ├── __init__.py                 <- Makes src a Python module
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
    ├── models/
    │   ├── predict_model.py        <- Code to run model inference with trained models          
    │   └── train_model.py          <- Code to train models
    │
    ├── pipeline/                   <- Execution Stages (The "Conductor")
    │
    └── utils/                      <- Common tools
        ├── common.py               <- Config readers
        ├── exception.py            <- Custom Error Handling (Reliability)
        ├── logger.py               <- Logging configuration
        ├── mlflow_config.py        <- MLflow configuration across modules
        └── paths.py                <- Define and manage file paths used throughout the project
