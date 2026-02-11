import os
import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DataIngestionConfig:
    raw_data_path: str = os.path.join("data", "raw", "data.csv")
    train_data_path: str = os.path.join("data", "processed", "train.csv")
    test_data_path: str = os.path.join("data", "processed", "test.csv")

class DataIngestion:
    def __init__(self):
        self.ingestion_config = DataIngestionConfig()

    def generate_synthetic_data(self, n_samples=1000):
        """Generates a synthetic dataset for credit risk assessment."""
        logger.info(f"Generating synthetic dataset with {n_samples} samples.")
        np.random.seed(42)
        
        data = {
            'revenue_growth': np.random.normal(0.05, 0.1, n_samples),  # 5% avg growth
            'ebitda_margin': np.random.normal(0.15, 0.05, n_samples),  # 15% avg margin
            'debt_to_equity': np.random.normal(1.5, 0.5, n_samples),   # 1.5 avg D/E
            'current_ratio': np.random.normal(1.2, 0.3, n_samples),    # 1.2 avg current ratio
            'sector_risk_score': np.random.randint(1, 10, n_samples),  # 1-10 sector risk
            'years_operating': np.random.randint(1, 50, n_samples),    # Years in business
        }
        
        df = pd.DataFrame(data)
        
        # Target: Risk Default (Binary)
        # Logic: Low margins + High Debt + High Sector Risk -> Higher Default Probability
        risk_score = (
            -2 * df['ebitda_margin'] +
            0.5 * df['debt_to_equity'] +
            0.1 * df['sector_risk_score'] -
            0.05 * df['years_operating']
        )
        
        # Convert score to probability (sigmoid) and then to binary class
        prob = 1 / (1 + np.exp(-risk_score))
        df['default_probability'] = prob
        df['target'] = (prob > 0.5).astype(int)
        
        return df

    def initiate_data_ingestion(self):
        logger.info("Entered the data ingestion method or component")
        try:
            # Check if raw data exists
            if not os.path.exists(self.ingestion_config.raw_data_path):
                logger.info("Raw data not found. Generating synthetic data.")
                df = self.generate_synthetic_data()
                os.makedirs(os.path.dirname(self.ingestion_config.raw_data_path), exist_ok=True)
                df.to_csv(self.ingestion_config.raw_data_path, index=False)
            else:
                df = pd.read_csv(self.ingestion_config.raw_data_path)
            
            logger.info("Read the dataset as dataframe")

            os.makedirs(os.path.dirname(self.ingestion_config.train_data_path), exist_ok=True)

            logger.info("Train test split initiated")
            train_set, test_set = train_test_split(df, test_size=0.2, random_state=42)

            train_set.to_csv(self.ingestion_config.train_data_path, index=False, header=True)
            test_set.to_csv(self.ingestion_config.test_data_path, index=False, header=True)

            logger.info("Ingestion of the data is completed")

            return (
                self.ingestion_config.train_data_path,
                self.ingestion_config.test_data_path
            )
        except Exception as e:
            logger.error(f"Error in data ingestion: {str(e)}")
            raise e

if __name__ == "__main__":
    obj = DataIngestion()
    obj.initiate_data_ingestion()
