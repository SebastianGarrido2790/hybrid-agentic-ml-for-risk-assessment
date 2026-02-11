"""
Configuration entities for the Agentic Credit Risk Assessment System (ACRAS).

This module defines dataclass entities to enforce strict type safety
and immutability to prevent attribute errors across different stages of the system.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_data_dir: Path
    financial_data_file: str
    pd_data_file: str
    unzip_dir: Path
    test_size: float
    val_size: float
    random_state: int
