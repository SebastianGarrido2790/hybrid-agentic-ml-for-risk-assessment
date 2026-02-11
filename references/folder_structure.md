Project-Name
├── LICENSE.txt                <- Project's license (Open-source if one is chosen)
├── README.md                  <- The top-level README for developers using this project.
├── .env                       <- Environment variables
├── .gitignore                 <- Files to ignore by Git
├── dvc.yaml                   <- The Pipeline Conductor
├── pyproject.toml             <- UV dependency definitions
├── Dockerfile                 <- Production container definition
│
├── .github/
│   └── workflows/             <- CI/CD (main.yaml)
│
├── config/
│   ├── config.yaml            <- System paths (artifacts/data)
│   └── params.yaml            <- Hyperparameters (K-neighbors, Chunk size)
│
├── data/
│   ├── external               <- Data from third party sources.
│   ├── interim                <- Intermediate data that has been transformed.
│   ├── processed              <- The final, canonical data sets for modeling.
│   └── raw                    <- The original, immutable data dump.
│
├── models/                    <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks/                 <- Jupyter notebooks.
│
├── references/                <- Data dictionaries, manuals, and all other explanatory materials.
│   └── folder_structure.md
│
├── reports/                   <- Generated analysis as HTML, PDF, LaTeX, etc.
│   ├── docs/                  <- Generated documents to be used in reporting
│   └── figures/               <- Generated graphics and figures to be used in reporting
│
└── src/                            <- Source code for use in this project.
    │
    ├── __init__.py                 <- Makes src a Python module
    │
    ├── data/
    │   ├── __init__.py
    │   ├── make_dataset.py         <- Scripts to download or generate data
    │   ├── data_ingestion.py
    │   └── data_transformation.py  <- (Hybrid: Pivot + Embeddings)
    │
    ├── features/
    │   ├── __init__.py
    │   └── build_features.py       <- Code to create features for modeling
    │
    ├── models/
    │   ├── __init__.py
    │   ├── predict_model.py        <- Code to run model inference with trained models          
    │   └── train_model.py          <- Code to train models
    │
    ├── utils/                      <- Common tools
    │   ├── common.py               <- Config readers
    │   ├── paths.py                <- Define and manage file paths used throughout the project
    │   ├── mlflow_config.py        <- MLflow configuration across modules
    │   └── exception.py            <- Custom Error Handling (Reliability)
    │
    └── visualization/
        ├── __init__.py
        ├── plot_settings.py
        └── visualize.py            <- Code to create visualizations