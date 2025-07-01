from matrx_connect.socket.core import SocketServiceBase


class {{cookiecutter.app_primary_service_name}}Service(SocketServiceBase):

    def __init__(self):
        self.stream_handler = None
        self.mic_check_message = None

        super().__init__(
            app_name="{{cookiecutter.app_name}}",
            service_name="{{cookiecutter.app_primary_service_name}}Service",
            log_level="INFO",
            batch_print=False,
        )


    async def process_task(self, task, task_context=None, process=True):
        return await self.execute_task(task, task_context, process)

    async def mic_check(self):
        await self.stream_handler.send_chunk(
            "[{{cookiecutter.app_primary_service_name}} SERVICE] Mic Check Response to: "
            + self.mic_check_message
        )
        await self.stream_handler.send_end()

