# {{cookiecutter.app_dirname}}/core/app_factory.py

from matrx_connect.socket import ServiceFactory
from matrx_connect.socket import configure_factory
from .{{cookiecutter.app_primary_service_name}} import {{cookiecutter.app_primary_service_name}}Service


class AppServiceFactory(ServiceFactory):
    def __init__(self):
        super().__init__()
        self.register_service("default_service", {{cookiecutter.app_primary_service_name}}Service)

        # Example of registering a single-instance service:
        # self.register_service(service_name="scrape_service", service_class=ScrapeService)

        # Example of registering a multi-instance service:
        # self.register_multi_instance_service(service_name="transcription_service", service_class=TranscriptionService)

configure_factory(AppServiceFactory)