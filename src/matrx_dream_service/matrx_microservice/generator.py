import json
from pathlib import Path
from typing import Dict, Any

import black
import os, subprocess, sys
from matrx_utils import FileManager, vcprint
from matrx_dream_service.matrx_microservice.contents import get_gitignore_content, get_conversions_content, \
    get_validation_content, get_app_py_content, get_settings_content, get_system_logger_content, \
    get_docker_file_content, get_entrypoint_sh_content, get_run_py_content, get_migrations_content, \
    get_admin_service_content, generate_readme
from matrx_utils import RESTRICTED_SERVICE_NAMES, \
    RESTRICTED_ENV_VAR_NAMES, RESTRICTED_TASK_AND_DEFINITIONS, RESTRICTED_FIELD_NAMES
from matrx_dream_service.matrx_microservice.default_template import default_config
from matrx_dream_service.matrx_microservice.merge_config import TemplateMerger
from matrx_dream_service.matrx_microservice.github_utils import orchestrate_repo_creation


class MicroserviceGenerator:
    def __init__(self, config_path: str = None, output_dir: str = None, create_github_repo: bool = False,
                 github_project_name: str = None, github_access: list[dict] = None, config: dict = None,
                 github_project_description: str = None, debug: bool = False):
        self.config_path = config_path
        self.output_dir = Path(output_dir) if output_dir else None
        self.config = self._load_config() if config_path else None

        self.create_github_repo = create_github_repo
        self.github_project_name = github_project_name
        self.github_access = github_access
        self.file_manager = FileManager("microservices")
        self.github_project_description = github_project_description
        self.debug = debug

        self.is_local = True

        if self.create_github_repo:
            self.is_local = False
            self.set_output_path(self.github_project_name)
            if not self.config:
                self.config = self.load_config_direct(config)

    def load_config_direct(self, config: dict):
        self._validate_config(config)
        system_config = default_config.copy()
        merger = TemplateMerger()
        merged_config = merger.merge(system_config, config)
        return merged_config

    def set_output_path(self, github_project_name: str):
        dirname = self.file_manager.generate_directoryname(random=True)
        self.output_dir = self.file_manager.get_full_path_from_base(root="temp", path=dirname)

    def _validate_config(self, config):
        conflicts = []

        # Validate environment variables (CASE SENSITIVE)
        env_vars = config.get("env", {})
        for env_name in env_vars.keys():
            if env_name in RESTRICTED_ENV_VAR_NAMES:
                conflicts.append(
                    f"Environment variable '{env_name}' is restricted")

        # Convert restricted sets to lowercase for case-insensitive comparison
        restricted_services_lower = {name.lower()
                                     for name in RESTRICTED_SERVICE_NAMES}
        restricted_tasks_defs_lower = {name.lower()
                                       for name in RESTRICTED_TASK_AND_DEFINITIONS}
        restricted_field_names = {name.lower()
                                  for name in RESTRICTED_FIELD_NAMES}
        # Validate schema definitions (CASE INSENSITIVE)
        schema = config.get("schema", {})
        definitions = schema.get("definitions", {})
        for def_name in definitions.keys():
            if def_name.lower() in restricted_tasks_defs_lower:
                conflicts.append(
                    f"Schema definition '{def_name}' is restricted (case insensitive)")

        # Validate schema tasks (services and task names) (CASE INSENSITIVE)
        tasks = schema.get("tasks", {})
        for service_name, service_tasks in tasks.items():
            if service_name.lower() in restricted_services_lower:
                conflicts.append(
                    f"Service name '{service_name}' is restricted (case insensitive)")

            for task_name, task_def in service_tasks.items():
                if task_name.lower() in restricted_tasks_defs_lower:
                    conflicts.append(
                        f"Task name '{task_name}' in service '{service_name}' is restricted (case insensitive)")
                for field_name in task_def.keys():
                    if field_name.lower() in restricted_field_names:
                        conflicts.append(
                            f"Field name '{field_name}' in service '{task_name}' is restricted (case insensitive)")

        # Raise error if any conflicts found
        if conflicts:
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(f"  - {conflict}" for conflict in conflicts))

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        self._validate_config(config)

        system_config = default_config.copy()
        merger = TemplateMerger()
        merged_config = merger.merge(system_config, config)

        return merged_config

    def generate_microservice(self):
        """Main function to generate the complete microservice"""

        vcprint(
            f"[matrx-dream-service] 📁 Target Directory: {self.output_dir}", color="bright_yellow", verbose=self.debug)
        vcprint(f"[matrx-dream-service] 📄 Config File: {self.config_path}", color="bright_yellow", verbose=self.debug)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        vcprint("\n[matrx-dream-service] 🔄 Starting microservice generation",
                color="bright_cyan", style="bold")

        self._generate_files()
        self._generate_gitignore()
        self._handle_databases()
        self._handle_env()
        self._handle_settings()
        self._generate_app_files()
        self._generate_other_schema_files()
        self._generate_service_directories()
        self._generate_core_files()
        self._generate_mcp()
        self._generate_docker_files()
        self._generate_root_files()
        self._format_project()
        self._generate_readme()

        if self.is_local:
            self._run_post_create_scripts()

        created_repo = None

        if self.create_github_repo:
            created_repo = orchestrate_repo_creation(self.github_project_name, self.github_project_description,
                                                     self.output_dir, access=self.github_access)

        return created_repo

    def _generate_readme(self):
        readme_content = generate_readme(self.config['settings'].get('app_name', 'Matrx'))
        full_path = self.output_dir / "README.md"
        with open(full_path, 'w') as f:
            f.write(readme_content)

    def _generate_files(self):
        """Generate all files listed in the files array"""
        files = self.config.get('files', [])
        if not files:
            return

        for file_path in files:
            full_path = self.output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()

        vcprint("[matrx-dream-service] ✅ Base files created", color="green", verbose=self.debug)

    def _generate_gitignore(self):
        gitignore_content = get_gitignore_content()
        full_path = self.output_dir / ".gitignore"

        with open(full_path, 'w') as f:
            f.write(gitignore_content)

        vcprint("[matrx-dream-service] ✅ .gitignore file generated", color="green", verbose=self.debug)

    def _handle_databases(self):
        databases = self.config.get('databases', [])
        if not databases:
            return

        env_path = self.output_dir / '.env'
        env_content = ""

        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()

        for index, db in enumerate(databases):
            db_name = db.get('db_name', f'database_{index}')
            env_content += f"\n# Database {index} - {db_name}\n"
            env_content += f"DB_USER_{index}={db.get('user')}\n"
            env_content += f"DB_PASS_{index}={db.get('password')}\n"
            env_content += f"DB_HOST_{index}={db.get('host')}\n"
            env_content += f"DB_NAME_{index}={db.get('database_name')}\n"

        # Write .env file
        with open(env_path, 'w') as f:
            f.write(env_content)

        # Generate database_registry.py
        db_conf_path = self.output_dir / 'database_registry.py'
        db_conf_path.parent.mkdir(parents=True, exist_ok=True)

        db_conf_content = '''from matrx_orm import DatabaseProjectConfig, register_database
from matrx_utils import settings

# Example of using DatabaseProjectConfig
'''

        def format_value(value, indent=0):
            spaces = "    " * indent

            if isinstance(value, dict):
                if not value:
                    return "{}"
                result = "{\n"
                for k, v in value.items():
                    if k == 'root' and isinstance(v, str):
                        if 'ADMIN_TS_ROOT' in v:
                            new_value = v.replace(
                                'ADMIN_TS_ROOT', '{settings.ADMIN_TS_ROOT}')
                            result += f"{spaces}    '{k}': f\"{new_value}\",\n"
                        elif 'ADMIN_PYTHON_ROOT' in v:
                            new_value = v.replace(
                                'ADMIN_PYTHON_ROOT', '{settings.ADMIN_PYTHON_ROOT}')
                            result += f"{spaces}    '{k}': f\"{new_value}\",\n"
                        else:
                            result += f"{spaces}    '{k}': \"{v}\",\n"
                    else:
                        formatted_v = format_value(v, indent + 1)
                        result += f"{spaces}    '{k}': {formatted_v},\n"
                result += f"{spaces}}}"
                return result
            elif isinstance(value, list):
                if not value:
                    return "[]"
                result = "[\n"
                for item in value:
                    if isinstance(item, str):
                        # Escape quotes properly
                        escaped_item = item.replace("'", "\\'")
                        result += f"{spaces}    '{escaped_item}',\n"
                    else:
                        formatted_item = format_value(item, indent + 1)
                        result += f"{spaces}    {formatted_item},\n"
                result += f"{spaces}]"
                return result
            elif isinstance(value, str):
                # Escape quotes properly
                escaped_value = value.replace("'", "\\'")
                return f"'{escaped_value}'"
            elif isinstance(value, (int, float, bool)):
                return str(value)
            else:
                return f"'{value}'"

        for index, db in enumerate(databases):
            db_project_name = db.get('name', f'database_{index}')
            db_port = db.get('port', 5432)
            manager_config_overrides = db.get('manager_config_overrides', {})

            formatted_manager_config = format_value(manager_config_overrides)
            db_conf_content += f"MANAGER_CONFIG_OVERRIDES_{index} = {formatted_manager_config}\n\n"

            db_conf_content += f'''my_db_{index} = DatabaseProjectConfig(name="{db_project_name}",
                                   user=settings.DB_USER_{index},
                                   alias="{db.get('alias', 'main')}",
                                   password=settings.DB_PASS_{index},
                                   host=settings.DB_HOST_{index},
                                   port=str({db_port}),
                                   database_name=settings.DB_NAME_{index},
                                   manager_config_overrides=MANAGER_CONFIG_OVERRIDES_{index})

register_database(my_db_{index})
'''

        with open(db_conf_path, 'w') as f:
            f.write(db_conf_content)

        vcprint("[matrx-dream-service] ✅ Database configuration completed", color="green", verbose=self.debug)

    def _handle_env(self):
        env_vars = self.config.get('env', {})
        settings = self.config.get('settings', {})

        # Create .env file
        env_path = self.output_dir / '.env'

        # Read existing content if file exists
        existing_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_content = f.read()

        env_content = existing_content

        # Add environment variables from env section
        if env_vars:
            env_content += "\n# Environment variables\n"
            for key, value in env_vars.items():
                if isinstance(value, bool):
                    env_content += f"{key}={str(value).lower()}\n"
                else:
                    env_content += f"{key}={value}\n"

        # Add settings converted to uppercase
        app_name = settings.get('app_name', '')
        app_version = settings.get('app_version', '')
        app_description = settings.get('app_description', '')
        app_primary_service_name = settings.get('app_primary_service_name', '')

        if app_name or app_version or app_description:
            env_content += "\n# Application settings\n"
            if app_name:
                env_content += f"APP_NAME={app_name}\n"
            if app_version:
                env_content += f"APP_VERSION={app_version}\n"
            if app_description:
                env_content += f"APP_DESCRIPTION={app_description}\n"
            if app_primary_service_name:
                env_content += f"APP_PRIMARY_SERVICE_NAME={app_primary_service_name}_service\n"

        with open(env_path, 'w') as f:
            f.write(env_content)

        vcprint("[matrx-dream-service] ✅ Environment variables completed", color="green", verbose=self.debug)

    def _handle_settings(self):
        """Handle settings and generate pyproject.toml"""
        settings = self.config.get('settings', {})
        pyproject_path = self.output_dir / 'pyproject.toml'
        dependencies = self.config.get('dependencies', [])

        app_name = settings.get('app_name', 'microservice')
        app_version = settings.get('app_version', '0.1.1')
        app_description = settings.get('app_description', 'A microservice')
        requires_python = settings.get('requires_python', '>=3.8')

        if dependencies:
            content = f'''[project]
name = "{app_name}"
version = "{app_version}"
description = "{app_description}"
readme = "README.md"
requires-python = "{requires_python}"
dependencies = [
'''

            for dep in dependencies:
                content += f'    "{dep}",\n'

            content += ']\n'

        with open(pyproject_path, 'w') as f:
            f.write(content)

        vcprint("[matrx-dream-service] ✅ pyproject.toml generated", color="green", verbose=self.debug)

    def _generate_app_files(self):
        """Generate app files based on schema configuration"""
        settings = self.config.get('settings', {})
        schema = self.config.get('schema', {})

        app_name = settings.get('app_name', 'microservice')
        app_primary_service_name = settings.get(
            'app_primary_service_name', 'default')

        # Use user schema directly - no merging
        schema = schema
        tasks_by_service = schema.get('tasks', {})

        # Create app_schema directory and schema.py
        app_schema_dir = self.output_dir / 'app_schema'
        app_schema_dir.mkdir(parents=True, exist_ok=True)

        schema_file_path = app_schema_dir / 'schema.py'
        schema_content = f'''from matrx_connect.socket.schema import register_schema
schema = {schema}
register_schema(schema)
    '''

        with open(schema_file_path, 'w') as f:
            f.write(schema_content)

        # Create services directory
        services_dir = self.output_dir / 'services'
        services_dir.mkdir(parents=True, exist_ok=True)

        for service_name, tasks in tasks_by_service.items():
            service_file_name = service_name.lower().replace('_service', '') + '_service.py'
            service_class_name = service_name.lower().replace(
                '_service', '').capitalize() + 'Service'
            clean_service_name = service_name.lower().replace('_service', '')
            orchestrator_class_name = clean_service_name.capitalize() + 'Orchestrator'

            # Collect fields from tasks (both direct fields and referenced definitions)
            all_fields = set()
            all_fields.add('mic_check_message')  # Always add mic_check_message

            for task_name, task_def in tasks.items():
                if isinstance(task_def, dict) and "$ref" not in task_def:
                    # Direct field definitions
                    all_fields.update(task_def.keys())
                elif isinstance(task_def, dict) and "$ref" in task_def:
                    # Resolve reference to get fields from definition
                    ref_path = task_def["$ref"].split("/")
                    if len(ref_path) == 2 and ref_path[0] == "definitions":
                        def_name = ref_path[1]
                        definitions = schema.get("definitions", {})
                        if def_name in definitions:
                            all_fields.update(definitions[def_name].keys())

            # Generate service file content
            service_content = f'''from matrx_connect.socket.core import SocketServiceBase
from src.{clean_service_name} import {orchestrator_class_name}

class {service_class_name}(SocketServiceBase):

    def __init__(self):
        self.stream_handler = None
'''

            # Add all field parameters to init
            for field in sorted(all_fields):
                service_content += f'        self.{field} = None\n'

            service_content += f'''
        # Initialize orchestrator
        self.{clean_service_name}_orchestrator = {orchestrator_class_name}()
        
        super().__init__(
            app_name="{app_name}",
            service_name="{service_class_name}",
            log_level="INFO",
            batch_print=False,
        )

    async def process_task(self, task, task_context=None, process=True):
        return await self.execute_task(task, task_context, process=True)

    async def mic_check(self):
        await self.stream_handler.send_chunk(
            "[{service_name} SERVICE] Mic Check Response to: "
            + self.mic_check_message
        )
        await self.stream_handler.send_end()
'''

            # Generate async methods for each task
            for task_name in tasks.keys():
                method_name = task_name.lower()
                if method_name != "mic_check":  # Skip mic_check as it's already added
                    service_content += f'''
    async def {method_name}(self):
        """Execute {task_name.lower()} task"""
        self.{clean_service_name}_orchestrator.add_stream_handler(self.stream_handler)  # Add stream handler to orchestrator for intermediate feedback.
        try:
            content = await self.{clean_service_name}_orchestrator.{method_name}()
            if content:
                await self.stream_handler.send_data(content)
            else:
                await self.stream_handler.send_error(
                    user_visible_message="Sorry, unable to complete the {task_name.lower()} task. Please try again later.",
                    message="Task returned no content",
                    error_type="task_failed"
                )
        except Exception as e:
            await self.stream_handler.send_error(
                user_visible_message="Sorry an error occurred, please try again later.",
                message=f"Task execution failed: {{e}}",
                error_type="task_failed"
            )
        finally:
            await self.stream_handler.send_end()
'''

            # Write service file
            service_file_path = services_dir / service_file_name
            with open(service_file_path, 'w') as f:
                f.write(service_content)

        # Generate app_factory.py
        app_factory_path = services_dir / 'app_factory.py'
        app_factory_content = '''from matrx_connect.socket import ServiceFactory
from matrx_connect.socket import configure_factory
from .admin_service import AdminService
'''

        # Import all service classes
        for service_name in tasks_by_service.keys():
            service_file_name = service_name.lower().replace('_service', '') + '_service'
            service_class_name = service_name.lower().replace(
                '_service', '').capitalize() + 'Service'
            app_factory_content += f'from .{service_file_name} import {service_class_name}\n'

        app_factory_content += '''

class AppServiceFactory(ServiceFactory):
    def __init__(self):
        super().__init__()
'''

        # Register all services
        for service_name in tasks_by_service.keys():
            service_class_name = service_name.lower().replace(
                '_service', '').capitalize() + 'Service'
            service_key = service_name.lower()
            if service_name == f"{app_primary_service_name.upper()}_SERVICE":
                app_factory_content += f'        self.register_service("default_service", {service_class_name})\n'
            else:
                app_factory_content += f'        self.register_service("{service_key}", {service_class_name})\n'

        app_factory_content += '''
        self.register_service(service_name="admin_service", service_class=AdminService)
        # Example of registering a single-instance service:
        # self.register_service(service_name="custom_service", service_class=CustomService)

        # Example of registering a multi-instance service:
        # self.register_multi_instance_service(service_name="worker_service", service_class=WorkerService)
    '''

        with open(app_factory_path, 'w') as f:
            f.write(app_factory_content)

        admin_service_file_name = services_dir / "admin_service.py"
        with open(admin_service_file_name, 'w') as f:
            f.write(get_admin_service_content())

        vcprint("[matrx-dream-service] ✅ Application schema and services generated", color="green", verbose=self.debug)

    def _generate_service_directories(self):
        schema = self.config.get('schema', {})
        tasks_by_service = schema.get('tasks', {})

        if not tasks_by_service:
            return

        src_dir = self.output_dir / 'src'
        src_dir.mkdir(parents=True, exist_ok=True)

        for service_name, tasks in tasks_by_service.items():
            # Convert SERVICE_NAME to service_name format
            clean_service_name = service_name.lower().replace('_service', '')
            service_dir = src_dir / clean_service_name
            service_dir.mkdir(parents=True, exist_ok=True)

            # Generate __init__.py
            orchestrator_class_name = clean_service_name.capitalize() + 'Orchestrator'
            init_content = f'''from .{clean_service_name}_orchestrator import {orchestrator_class_name}
__all__ = ["{orchestrator_class_name}"]
    '''
            with open(service_dir / '__init__.py', 'w') as f:
                f.write(init_content)

            # Generate orchestrator class
            orchestrator_content = f'''class {orchestrator_class_name}:
    """
    Orchestrator for {clean_service_name} service operations.
    This class handles the core business logic for {clean_service_name} tasks.
    """

    def __init__(self):
        self.stream_handler = None
        
        
    def add_stream_handler(self, stream_handler):
        self.stream_handler = stream_handler
    '''

            # Generate method for each task
            for task_name in tasks.keys():
                method_name = task_name.lower()
                if method_name != "mic_check":  # Don't generate mic_check in orchestrator
                    orchestrator_content += f'''
    async def {method_name}(self):
        """
        Handle {task_name.lower()} task.
        """
        # TODO: Replace this placeholder with actual implementation

        return {{
            "task": "{task_name.lower()}",
            "service": "{clean_service_name}",
            "message": "This is a placeholder for {task_name.lower()} task",
        }}
    '''

            with open(service_dir / f'{clean_service_name}_orchestrator.py', 'w') as f:
                f.write(orchestrator_content)

        vcprint("[matrx-dream-service] ✅ Service directories and orchestrators generated", color="green",
                verbose=self.debug)

    def _generate_other_schema_files(self):
        # Create app_schema directory
        app_schema_dir = self.output_dir / 'app_schema'
        app_schema_dir.mkdir(parents=True, exist_ok=True)

        # Generate conversion_functions.py
        conversion_content = get_conversions_content()
        with open(app_schema_dir / 'conversion_functions.py', 'w') as f:
            f.write(conversion_content)

        # Generate validation_functions.py
        validation_content = get_validation_content()
        with open(app_schema_dir / 'validation_functions.py', 'w') as f:
            f.write(validation_content)

        init_content = '''from .schema import *
from .conversion_functions import *
from .validation_functions import *
'''
        with open(app_schema_dir / '__init__.py', 'w') as f:
            f.write(init_content)

        vcprint("[matrx-dream-service] ✅ Schema validation and conversion functions generated", color="green",
                verbose=self.debug)

    def _generate_core_files(self):
        settings = self.config.get('settings', {})
        app_name = settings.get('app_name', 'microservice')
        app_description = settings.get('app_description')
        app_version = settings.get('app_version')

        # Create core directory
        core_dir = self.output_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)

        # Generate app.py
        app_content = get_app_py_content()
        with open(core_dir / 'app.py', 'w', encoding="utf-8") as f:
            f.write(app_content)

        # Generate settings.py
        settings_content = get_settings_content(app_name)
        with open(core_dir / 'settings.py', 'w') as f:
            f.write(settings_content)

        # Generate system_logger.py
        system_logger_content = get_system_logger_content()
        with open(core_dir / 'system_logger.py', 'w') as f:
            f.write(system_logger_content)

        vcprint("[matrx-dream-service] ✅ Core application files generated", color="green", verbose=self.debug)

    def _generate_mcp(self):
        schema = self.config.get('schema', {})
        tasks_by_service = schema.get('tasks', {})
        definitions = schema.get('definitions', {})

        if not tasks_by_service:
            return

        mcp_dir = self.output_dir / 'mcp_server'
        mcp_dir.mkdir(parents=True, exist_ok=True)

        init_content = '''from matrx_connect.mcp_server import tool_registry
from matrx_connect.mcp_server.tools import register_default_tools

'''

        register_functions = []

        for service_name, tasks in tasks_by_service.items():
            if 'admin' in service_name.lower():
                continue  # Skip admin service

            clean_service_name = service_name.lower().replace('_service', '')
            service_mcp_dir = mcp_dir / clean_service_name
            service_mcp_dir.mkdir(parents=True, exist_ok=True)

            tool_content = '''import traceback
from typing import Any, Dict, Union

from src.{clean_service_name} import {orchestrator_class_name}

'''.format(clean_service_name=clean_service_name,
           orchestrator_class_name=clean_service_name.capitalize() + 'Orchestrator')

            tool_functions = []
            register_calls = []

            for task_name, task_def in tasks.items():
                if task_name.lower() == 'mic_check':
                    continue  # Skip mic_check

                method_name = task_name.lower()
                tool_name = f'{clean_service_name}_{method_name}_tool'

                # Get fields
                if '$ref' in task_def:
                    ref_def_name = task_def['$ref'].split('/')[-1]
                    fields = definitions.get(ref_def_name, {})
                else:
                    fields = task_def

                # Generate tool function
                tool_content += f'async def {tool_name}(args: Dict[str, Any]) -> Dict[str, Any]:\n'
                tool_content += '    """\n'
                tool_content += f'    Perform {method_name} operation.\n'
                tool_content += '    \n'
                tool_content += '    Args:\n'
                tool_content += '        args: Dictionary containing parameters.\n'
                tool_content += '    \n'
                tool_content += '    Returns:\n'
                tool_content += '        Dictionary with status and result/error information\n'
                tool_content += '    """\n'
                tool_content += '    try:\n'
                tool_content += '        orchestrator = {orchestrator_class_name}()\n'.format(
                    orchestrator_class_name=clean_service_name.capitalize() + 'Orchestrator')
                tool_content += f'        result = await orchestrator.{method_name}()\n'
                tool_content += '        return {\n'
                tool_content += '            "status": "success",\n'
                tool_content += '            "result": result\n'
                tool_content += '        }\n'
                tool_content += '    except Exception as e:\n'
                tool_content += '        return {\n'
                tool_content += '            "status": "error",\n'
                tool_content += '            "error": f"Unexpected error: {{str(e)}}"\n'
                tool_content += '        }\n\n'

                tool_functions.append(tool_name)

                # Register for this tool
                register_calls.append(f'    tool_registry.register_tool(\n'
                                      f'        name="{tool_name}",\n'
                                      f'        description="Perform {method_name} operation in {clean_service_name} service.",\n'
                                      '        parameters={\n')
                for field_name, field_def in fields.items():
                    param_type = field_def.get('type', 'string')
                    desc = field_def.get('description', 'No description')
                    required = field_def.get('required', False)
                    register_calls.append(f'            "{field_name}": {{\n'
                                          f'                "type": "{param_type}",\n'
                                          f'                "description": "{desc}",\n'
                                          f'                "required": True\n'
                                          '            },\n')
                    if 'default' in field_def:
                        default_str = repr(field_def['default'])
                        register_calls[-1] = register_calls[-1].rstrip(
                            ',\n') + ',\n' + f'                "default": {default_str}\n            }},\n'
                register_calls.append('        },\n'
                                      '        output_schema={\n'
                                      '            "type": "object",\n'
                                      '            "properties": {\n'
                                      '                "status": {"type": "string"},\n'
                                      '                "result": {"type": "object"},\n'
                                      '                "error": {"type": "string"}\n'
                                      '            }\n'
                                      '        },\n'
                                      '        annotations=[\n'
                                      '            {\n'
                                      '                "type": "usage_hint",\n'
                                      '                "value": "Use this tool to perform {method_name} in {clean_service_name} service."\n'
                                      '            }\n'
                                      '        ],\n'
                                      f'        function={tool_name}\n'
                                      '    )\n')

            # Add register function
            register_func_name = f'register_{clean_service_name}_tools'
            tool_content += f'def {register_func_name}(tool_registry):\n'
            tool_content += '    """\n'
            tool_content += f'    Register tools for {clean_service_name} service.\n'
            tool_content += '    """\n'
            tool_content += ''.join(register_calls) + '\n'

            # __all__
            all_items = tool_functions + [register_func_name]
            tool_content += f'__all__ = {all_items}\n'

            # Write tool file
            tool_file_path = service_mcp_dir / f'{clean_service_name}.py'
            with open(tool_file_path, 'w') as f:
                f.write(tool_content)

            # Add to init
            init_content += f'from .{clean_service_name}.{clean_service_name} import {register_func_name}\n'

            register_functions.append(register_func_name)

        # Add register all in init
        init_content += '\ndef register_all_mcp_tools():\n    register_default_tools()\n'
        for reg_func in register_functions:
            init_content += f'    {reg_func}(tool_registry)\n'

        with open(mcp_dir / '__init__.py', 'w') as f:
            f.write(init_content)

        vcprint("[matrx-dream-service] ✅ MCP directories and tools generated", color="green", verbose=self.debug)

    def _generate_docker_files(self):
        settings = self.config.get('settings', {})
        app_name = settings.get('app_name')

        # Generate .python-version
        python_version_content = "3.13"
        with open(self.output_dir / '.python-version', 'w') as f:
            f.write(python_version_content)

        # Generate Dockerfile
        dockerfile_content = get_docker_file_content(app_name)
        with open(self.output_dir / 'Dockerfile', 'w') as f:
            f.write(dockerfile_content)

        # Generate entrypoint.sh
        entrypoint_content = get_entrypoint_sh_content()
        with open(self.output_dir / 'entrypoint.sh', 'w') as f:
            f.write(entrypoint_content)

        vcprint("[matrx-dream-service] ✅ Docker configuration files generated", color="green", verbose=self.debug)

    def _generate_root_files(self):
        settings = self.config.get('settings', {})
        app_name = settings.get('app_name')

        migrations_content = get_migrations_content(app_name)
        with open(self.output_dir / 'generate_model_files.py', 'w') as f:
            f.write(migrations_content)

        run_content = get_run_py_content()
        with open(self.output_dir / 'run.py', 'w') as f:
            f.write(run_content)

        vcprint("[matrx-dream-service] ✅ Root level files generated", color="green", verbose=self.debug)

    def _format_py_file(self, fp):
        file_path = Path(fp)

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        try:
            formatted_code = black.format_file_contents(
                code,
                fast=False,  # Run in safe mode to ensure correctness
                mode=black.FileMode(
                    target_versions={black.TargetVersion.PY38},
                    line_length=80,
                ),
            )
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_code)

        except black.NothingChanged:
            pass

    def _format_project(self):
        directory = self.output_dir

        for fp in directory.glob("**/*.py"):
            try:
                self._format_py_file(fp)
            except (black.InvalidInput, ValueError) as e:
                pass

        vcprint("[matrx-dream-service] ✅ Project formatted", color="green", verbose=self.debug)

    def _run_post_create_scripts(self):

        scripts = ["uv sync",
                   "uv run --active generate_model_files.py --create-all true",
                   "git init ."
                   ]

        original_dir = os.getcwd()
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSFSENCODING'] = '0'

        try:
            os.chdir(self.output_dir)
            vcprint(f"📁 Changed working directory to: {self.output_dir}", color="light_blue")

            for i, script in enumerate(scripts, 1):
                vcprint(f"\n{'─' * 60}", color="bright_cyan")
                vcprint(f"⚡ Executing script {i}/{len(scripts)}: {script}", color="bright_cyan", style="bold")
                vcprint(f"{'─' * 60}", color="bright_cyan")

                cmd_parts = script.split()
                try:
                    process = subprocess.Popen(
                        cmd_parts,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=1,
                        env=env,
                        encoding='utf-8',
                        errors='replace'
                    )
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            print(output.strip())
                            sys.stdout.flush()
                    return_code = process.poll()

                    if return_code == 0:
                        vcprint(f"✅ Script {i} completed successfully: {script}", color="green", style="bold")
                    else:
                        vcprint(f"❌ Script {i} failed with return code {return_code}: {script}", color="red",
                                style="bold")
                except FileNotFoundError:
                    vcprint(f"❌ Command not found: {script}", color="red")
                except Exception as e:
                    vcprint(f"❌ Error executing script '{script}': {e}", "red")
        finally:
            os.chdir(original_dir)
