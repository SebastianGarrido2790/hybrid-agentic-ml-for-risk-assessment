from src.config.configuration import ConfigurationManager
from src.components.model_registration import ModelRegistration
from src.utils.common import logger


class ModelRegistrationTrainingPipeline:
    def main(self):
        try:
            config = ConfigurationManager()
            model_registration_config = config.get_model_registration_config()
            model_registration = ModelRegistration(config=model_registration_config)
            model_registration.log_into_mlflow()
        except Exception as e:
            raise e


if __name__ == "__main__":
    try:
        logger.info(">>>>>> stage Model Registration started <<<<<<")
        obj = ModelRegistrationTrainingPipeline()
        obj.main()
        logger.info(">>>>>> stage Model Registration completed <<<<<<\n\nx==========x")
    except Exception as e:
        logger.exception(e)
        raise e
