from matrx_orm import DatabaseProjectConfig, register_database
from matrx_utils import settings

# Example of using DatabaseProjectConfig

CODE_BASICS = {}
MANAGER_CONFIG_OVERRIDES = {}

my_db = DatabaseProjectConfig(name="{{cookiecutter.app_name}}",
                               user=settings.DB_USER,
                               password=settings.DB_PASS,
                               host=settings.DB_HOST,
                               port=settings.DB_PORT,
                               database_name=settings.DB_NAME,
                               code_basics=CODE_BASICS,
                               manager_config_overrides=MANAGER_CONFIG_OVERRIDES)

register_database(my_db)