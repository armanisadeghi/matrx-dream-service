from dotenv import load_dotenv
load_dotenv()
from matrx_dream_service.matrx_microservice import MicroserviceGenerator

MicroserviceGenerator(config_path=r"D:\work\matrx\matrx-dream-service\temp\base_config-backup.json",
                      output_dir=f"D:/work/matrx/generated/new",
                      ).generate_microservice()
