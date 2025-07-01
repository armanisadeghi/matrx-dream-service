import logging
from dotenv import load_dotenv
from socketio import ASGIApp

from matrx_utils import vcprint, settings
from matrx_connect import sio, get_user_session_namespace ,configure_factory
from matrx_connect.api import create_app
from services.app_factory import AppServiceFactory

load_dotenv()

import core.system_logger

logger = logging.getLogger("app")
logger.info("Starting application")

# Initialize service factory
configure_factory(AppServiceFactory)
vcprint("Service factory initialized", color="bright_teal")

# Create FastAPI app
app = create_app(settings.APP_NAME, settings.APP_DESCRIPTION, settings.APP_VERSION)
vcprint("FastAPI application created", color="green")

# Configure Socket.IO
socketio_app = ASGIApp(sio)
user_session_namespace = get_user_session_namespace()
sio.register_namespace(user_session_namespace)
app.mount("/socket.io", socketio_app)

vcprint("Socket.IO configured", color="green")
