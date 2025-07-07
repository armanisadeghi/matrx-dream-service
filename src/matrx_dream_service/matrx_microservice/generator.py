import json
from pathlib import Path
from typing import Dict, Any
import subprocess
import os
import sys
import black

from matrx_utils import vcprint
from matrx_dream_service.matrx_microservice.contents import get_gitignore_content, get_conversions_content, \
    get_validation_content, get_app_py_content, get_settings_content, get_system_logger_content, \
    get_docker_file_content, get_entrypoint_sh_content, get_run_py_content, get_migrations_content, get_admin_service_content
from matrx_utils import RESTRICTED_SERVICE_NAMES, \
    RESTRICTED_ENV_VAR_NAMES, RESTRICTED_TASK_AND_DEFINITIONS, RESTRICTED_FIELD_NAMES
from matrx_dream_service.matrx_microservice.default_template import default_config
from matrx_dream_service.matrx_microservice.merge_config import TemplateMerger

class MicroserviceGenerator:
    def __init__(self, config_path: str, output_dir: str):
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.config = self._load_config()

    def _validate_config(self, config):
        conflicts = []

        # Validate environment variables (CASE SENSITIVE)
        env_vars = config.get("env", {})
        for env_name in env_vars.keys():
            if env_name in RESTRICTED_ENV_VAR_NAMES:
                conflicts.append(f"Environment variable '{env_name}' is restricted")

        # Convert restricted sets to lowercase for case-insensitive comparison
        restricted_services_lower = {name.lower() for name in RESTRICTED_SERVICE_NAMES}
        restricted_tasks_defs_lower = {name.lower() for name in RESTRICTED_TASK_AND_DEFINITIONS}
        restricted_field_names = {name.lower() for name in RESTRICTED_FIELD_NAMES}
        # Validate schema definitions (CASE INSENSITIVE)
        schema = config.get("schema", {})
        definitions = schema.get("definitions", {})
        for def_name in definitions.keys():
            if def_name.lower() in restricted_tasks_defs_lower:
                conflicts.append(f"Schema definition '{def_name}' is restricted (case insensitive)")

        # Validate schema tasks (services and task names) (CASE INSENSITIVE)
        tasks = schema.get("tasks", {})
        for service_name, service_tasks in tasks.items():
            if service_name.lower() in restricted_services_lower:
                conflicts.append(f"Service name '{service_name}' is restricted (case insensitive)")

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
                f"Configuration validation failed:\n" + "\n".join(f"  - {conflict}" for conflict in conflicts))

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        vcprint("🔧 Loading configuration...", color="cyan", style="bold")
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        vcprint(f"✅ Configuration loaded successfully from: {self.config_path}", color="green")

        self._validate_config(config)

        system_config = default_config.copy()
        merger = TemplateMerger()
        merged_config = merger.merge(system_config, config)

        vcprint(merged_config, title="Merged configuration", color="bright_teal")
        return merged_config

    def generate_microservice(self):
        """Main function to generate the complete microservice"""
        vcprint("\n" + "=" * 80, color="bright_magenta", style="bold")
        vcprint("🚀 MATRX MICROSERVICE GENERATOR", color="bright_magenta", style="bold")
        vcprint("=" * 80, color="bright_magenta", style="bold")

        vcprint(f"📁 Target Directory: {self.output_dir}", color="bright_yellow")
        vcprint(f"📄 Config File: {self.config_path}", color="bright_yellow")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        vcprint("✅ Output directory created/verified", color="green")

        vcprint("\n🔄 Starting microservice generation process...", color="bright_cyan", style="bold")

        self._generate_files()
        self._generate_gitignore()
        self._handle_databases()
        self._handle_env()
        self._handle_settings()
        self._generate_app_files()
        self._generate_other_schema_files()
        self._generate_service_directories()
        self._generate_core_files()
        self._generate_docker_files()
        self._generate_root_files()
        self._format_project()

        self._run_post_create_scripts()

        vcprint("\n" + "=" * 80, color="bright_green", style="bold")
        vcprint("🎉 MICROSERVICE GENERATION COMPLETE!", color="bright_green", style="bold")
        vcprint("=" * 80, color="bright_green", style="bold")

    def _generate_files(self):
        """Generate all files listed in the files array"""
        vcprint("\n📋 STEP 1: Creating base file structure", color="bright_blue", style="bold")

        files = self.config.get('files', [])
        if not files:
            vcprint("⚠️  No files specified in configuration", color="yellow")
            return

        vcprint(f"📝 Creating {len(files)} files from configuration...", color="blue")

        for file_path in files:
            full_path = self.output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            vcprint(f"  ✓ Created: {file_path}", color="light_green")

        vcprint(f"✅ Successfully created {len(files)} base files", color="green")

    def _generate_gitignore(self):
        vcprint("\n📋 STEP 2: Generating .gitignore file", color="bright_blue", style="bold")

        gitignore_content = get_gitignore_content()
        full_path = self.output_dir / ".gitignore"

        with open(full_path, 'w') as f:
            f.write(gitignore_content)

        vcprint("✅ .gitignore file generated successfully", color="green")

    def _handle_databases(self):
        vcprint("\n📋 STEP 3: Configuring database connections", color="bright_blue", style="bold")

        databases = self.config.get('databases', [])
        if not databases:
            vcprint("ℹ️  No databases configured, skipping database setup", color="light_blue")
            return

        vcprint(f"🗄️  Configuring {len(databases)} database(s)...", color="blue")

        env_path = self.output_dir / '.env'
        env_content = ""

        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            vcprint("  📄 Existing .env file found, appending database config", color="light_blue")

        for index, db in enumerate(databases):
            db_name = db.get('db_name', f'database_{index}')
            env_content += f"\n# Database {index} - {db_name}\n"
            env_content += f"DB_USER_{index}={db.get('db_user')}\n"
            env_content += f"DB_PASS_{index}={db.get('db_password')}\n"
            env_content += f"DB_HOST_{index}={db.get('db_host')}\n"
            env_content += f"DB_NAME_{index}={db.get('db_name')}\n"

            vcprint(f"  ✓ Database {index}: {db_name} configured", color="light_green")

        # Write .env file
        with open(env_path, 'w') as f:
            f.write(env_content)
        vcprint("  📝 Database environment variables written to .env", color="light_green")

        # Generate db_conf.py
        db_conf_path = self.output_dir / 'database' / 'db_conf.py'
        db_conf_path.parent.mkdir(parents=True, exist_ok=True)
        vcprint("  📁 Created database configuration directory", color="light_green")

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
                            new_value = v.replace('ADMIN_TS_ROOT', '{settings.ADMIN_TS_ROOT}')
                            result += f"{spaces}    '{k}': f\"{new_value}\",\n"
                        elif 'ADMIN_PYTHON_ROOT' in v:
                            new_value = v.replace('ADMIN_PYTHON_ROOT', '{settings.ADMIN_PYTHON_ROOT}')
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
            db_project_name = db.get('db_project_name', f'database_{index}')
            db_port = db.get('db_port', 5432)
            code_basics = db.get('code_basics', {})
            manager_config_overrides = db.get('manager_configs', {})

            formatted_code_basics = format_value(code_basics)
            db_conf_content += f"CODE_BASICS_{index} = {formatted_code_basics}\n\n"

            formatted_manager_config = format_value(manager_config_overrides)
            db_conf_content += f"MANAGER_CONFIG_OVERRIDES_{index} = {formatted_manager_config}\n\n"

            db_conf_content += f'''my_db_{index} = DatabaseProjectConfig(name="{db_project_name}",
                                   user=settings.DB_USER_{index},
                                   password=settings.DB_PASS_{index},
                                   host=settings.DB_HOST_{index},
                                   port=str({db_port}),
                                   database_name=settings.DB_NAME_{index},
                                   code_basics=CODE_BASICS_{index},
                                   manager_config_overrides=MANAGER_CONFIG_OVERRIDES_{index})

register_database(my_db_{index})
'''

        with open(db_conf_path, 'w') as f:
            f.write(db_conf_content)

        vcprint("  📝 Database configuration file (db_conf.py) generated", color="light_green")
        vcprint(f"✅ Database configuration completed for {len(databases)} database(s)", color="green")

    def _handle_env(self):
        vcprint("\n📋 STEP 4: Setting up environment variables", color="bright_blue", style="bold")

        env_vars = self.config.get('env', {})
        settings = self.config.get('settings', {})

        # Create .env file
        env_path = self.output_dir / '.env'

        # Read existing content if file exists
        existing_content = ""
        if env_path.exists():
            with open(env_path, 'r') as f:
                existing_content = f.read()
            vcprint("  📄 Found existing .env file, preserving current content", color="light_blue")

        env_content = existing_content

        # Add environment variables from env section
        if env_vars:
            vcprint(f"  🔧 Adding {len(env_vars)} environment variables...", color="blue")
            env_content += "\n# Environment variables\n"
            for key, value in env_vars.items():
                if isinstance(value, bool):
                    env_content += f"{key}={str(value).lower()}\n"
                else:
                    env_content += f"{key}={value}\n"
                vcprint(f"    ✓ {key} = {value}", color="light_green")

        # Add settings converted to uppercase
        app_name = settings.get('app_name', '')
        app_version = settings.get('app_version', '')
        app_description = settings.get('app_description', '')
        app_primary_service_name = settings.get('app_primary_service_name', '')

        if app_name or app_version or app_description:
            vcprint("  ⚙️  Adding application settings to environment...", color="blue")
            env_content += "\n# Application settings\n"
            if app_name:
                env_content += f"APP_NAME={app_name}\n"
                vcprint(f"    ✓ APP_NAME = {app_name}", color="light_green")
            if app_version:
                env_content += f"APP_VERSION={app_version}\n"
                vcprint(f"    ✓ APP_VERSION = {app_version}", color="light_green")
            if app_description:
                env_content += f"APP_DESCRIPTION={app_description}\n"
                vcprint(f"    ✓ APP_DESCRIPTION = {app_description}", color="light_green")
            if app_primary_service_name:
                env_content += f"APP_PRIMARY_SERVICE_NAME={app_primary_service_name}_service\n"
                vcprint(f"    ✓ APP_PRIMARY_SERVICE_NAME = {app_primary_service_name}", color="light_green")

        with open(env_path, 'w') as f:
            f.write(env_content)

        vcprint("✅ Environment variables configuration completed", color="green")

    def _handle_settings(self):
        """Handle settings and generate pyproject.toml"""
        vcprint("\n📋 STEP 5: Generating project settings (pyproject.toml)", color="bright_blue", style="bold")

        settings = self.config.get('settings', {})
        pyproject_path = self.output_dir / 'pyproject.toml'
        dependencies = self.config.get('dependencies', [])

        app_name = settings.get('app_name', 'microservice')
        app_version = settings.get('app_version', '0.1.0')
        app_description = settings.get('app_description', 'A microservice')
        requires_python = settings.get('requires_python', '>=3.8')
        additional_content = settings.get('pyproject_additional_content', '')

        vcprint(f"  📦 Project: {app_name} v{app_version}", color="blue")
        vcprint(f"  📝 Description: {app_description}", color="blue")
        vcprint(f"  🐍 Python requirement: {requires_python}", color="blue")

        if dependencies:
            vcprint(f"  📋 Dependencies: {len(dependencies)} packages", color="blue")
            for dep in dependencies:
                vcprint(f"    ✓ {dep}", color="light_green")
        else:
            vcprint("  ℹ️  No additional dependencies specified", color="light_blue")

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

        vcprint("✅ pyproject.toml generated successfully", color="green")

    def _generate_app_files(self):
        """Generate app files based on schema configuration"""
        vcprint("\n📋 STEP 6: Generating application schema and services", color="bright_blue", style="bold")

        settings = self.config.get('settings', {})
        user_schema = self.config.get('schema', {})

        app_name = settings.get('app_name', 'microservice')
        app_primary_service_name = settings.get('app_primary_service_name', 'default')

        vcprint(f"  🏗️  Building schema for application: {app_name}", color="blue")
        vcprint(f"  🎯 Primary service: {app_primary_service_name}", color="blue")

        # Use user schema directly - no merging
        schema = user_schema
        tasks_by_service = schema.get('tasks', {})

        vcprint(f"  📝 Processing {len(tasks_by_service)} services from user schema", color="blue")

        # Create app_schema directory and schema.py
        app_schema_dir = self.output_dir / 'app_schema'
        app_schema_dir.mkdir(parents=True, exist_ok=True)
        vcprint("  📁 Created app_schema directory", color="light_green")

        schema_file_path = app_schema_dir / 'schema.py'
        schema_content = f'''from matrx_connect.socket.schema import register_schema
schema = {schema}
register_schema(schema)
    '''

        with open(schema_file_path, 'w') as f:
            f.write(schema_content)
        vcprint("  📝 Schema registered in schema.py", color="light_green")

        # Create services directory
        services_dir = self.output_dir / 'services'
        services_dir.mkdir(parents=True, exist_ok=True)
        vcprint("  📁 Created services directory", color="light_green")

        # Generate service files for each service in tasks
        vcprint(f"  🔧 Generating {len(tasks_by_service)} service files...", color="blue")
        for service_name, tasks in tasks_by_service.items():
            service_file_name = service_name.lower().replace('_service', '') + '_service.py'
            service_class_name = service_name.lower().replace('_service', '').capitalize() + 'Service'
            clean_service_name = service_name.lower().replace('_service', '')
            orchestrator_class_name = clean_service_name.capitalize() + 'Orchestrator'

            vcprint(f"    ⚙️  Generating service: {service_class_name}", color="blue")

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
        return await self.execute_task(task, task_context, process)

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

            vcprint(f"      ✓ {service_file_name} with {len(tasks)} tasks", color="light_green")

        # Generate app_factory.py
        vcprint("  🏭 Generating service factory...", color="blue")
        app_factory_path = services_dir / 'app_factory.py'
        app_factory_content = '''from matrx_connect.socket import ServiceFactory
from matrx_connect.socket import configure_factory
from .admin_service import AdminService
'''

        # Import all service classes
        for service_name in tasks_by_service.keys():
            service_file_name = service_name.lower().replace('_service', '') + '_service'
            service_class_name = service_name.lower().replace('_service', '').capitalize() + 'Service'
            app_factory_content += f'from .{service_file_name} import {service_class_name}\n'

        app_factory_content += '''

class AppServiceFactory(ServiceFactory):
    def __init__(self):
        super().__init__()
'''

        # Register all services
        for service_name in tasks_by_service.keys():
            service_class_name = service_name.lower().replace('_service', '').capitalize() + 'Service'
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

        vcprint("  ✓ Service factory (app_factory.py) generated", color="light_green")
        vcprint("✅ Application schema and services generation completed", color="green")

        admin_service_file_name = services_dir / "admin_service.py"
        with open(admin_service_file_name, 'w') as f:
            f.write(get_admin_service_content())

    def _generate_service_directories(self):
        """Generate service directories with orchestrator classes"""
        vcprint("\n📋 STEP 7.5: Generating service directories and orchestrators", color="bright_blue", style="bold")

        schema = self.config.get('schema', {})
        tasks_by_service = schema.get('tasks', {})

        if not tasks_by_service:
            vcprint("ℹ️  No services found in schema, skipping service directories", color="light_blue")
            return

        src_dir = self.output_dir / 'src'
        src_dir.mkdir(parents=True, exist_ok=True)
        vcprint("  📁 Created src directory", color="light_green")

        vcprint(f"  🔧 Generating {len(tasks_by_service)} service directories...", color="blue")

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

            vcprint(f"    ✓ {clean_service_name}/ directory with {len(tasks)} orchestrator methods",
                    color="light_green")

        vcprint("✅ Service directories and orchestrators generation completed", color="green")

    def _generate_other_schema_files(self):
        """Generate app schema files"""
        vcprint("\n📋 STEP 7: Generating schema validation and conversion functions", color="bright_blue", style="bold")

        # Create app_schema directory
        app_schema_dir = self.output_dir / 'app_schema'
        app_schema_dir.mkdir(parents=True, exist_ok=True)

        vcprint("  🔧 Generating conversion functions...", color="blue")
        # Generate conversion_functions.py
        conversion_content = get_conversions_content()
        with open(app_schema_dir / 'conversion_functions.py', 'w') as f:
            f.write(conversion_content)
        vcprint("  ✓ conversion_functions.py generated", color="light_green")

        vcprint("  🔧 Generating validation functions...", color="blue")
        # Generate validation_functions.py
        validation_content = get_validation_content()
        with open(app_schema_dir / 'validation_functions.py', 'w') as f:
            f.write(validation_content)
        vcprint("  ✓ validation_functions.py generated", color="light_green")

        init_content = '''from .schema import *
from .conversion_functions import *
from .validation_functions import *
'''
        with open(app_schema_dir / '__init__.py', 'w') as f:
            f.write(init_content)
        vcprint("  ✓ app_schema/__init__.py generated", color="light_green")

        vcprint("✅ Schema validation and conversion functions completed", color="green")

    def _generate_core_files(self):
        """Generate core application files"""
        vcprint("\n📋 STEP 8: Generating core application files", color="bright_blue", style="bold")

        settings = self.config.get('settings', {})
        app_name = settings.get('app_name', 'microservice')
        app_description = settings.get('app_description')
        app_version = settings.get('app_version')

        # Create core directory
        core_dir = self.output_dir / 'core'
        core_dir.mkdir(parents=True, exist_ok=True)
        vcprint("  📁 Created core directory", color="light_green")

        vcprint("  🔧 Generating core application files...", color="blue")

        # Generate app.py
        app_content = get_app_py_content()
        with open(core_dir / 'app.py', 'w') as f:
            f.write(app_content)
        vcprint("  ✓ app.py - Main application entry point", color="light_green")

        # Generate settings.py
        settings_content = get_settings_content(app_name)
        with open(core_dir / 'settings.py', 'w') as f:
            f.write(settings_content)
        vcprint("  ✓ settings.py - Application configuration", color="light_green")

        # Generate system_logger.py
        system_logger_content = get_system_logger_content()
        with open(core_dir / 'system_logger.py', 'w') as f:
            f.write(system_logger_content)
        vcprint("  ✓ system_logger.py - Logging configuration", color="light_green")

        vcprint("✅ Core application files generation completed", color="green")

    def _generate_docker_files(self):
        """Generate Docker related files"""
        vcprint("\n📋 STEP 9: Generating Docker configuration files", color="bright_blue", style="bold")

        settings = self.config.get('settings', {})
        app_name = settings.get('app_name')

        vcprint("  🐳 Creating Docker configuration files...", color="blue")

        # Generate .python-version
        python_version_content = "3.13"
        with open(self.output_dir / '.python-version', 'w') as f:
            f.write(python_version_content)
        vcprint("  ✓ .python-version - Python version specification", color="light_green")

        # Generate Dockerfile
        dockerfile_content = get_docker_file_content(app_name)
        with open(self.output_dir / 'Dockerfile', 'w') as f:
            f.write(dockerfile_content)
        vcprint("  ✓ Dockerfile - Container build instructions", color="light_green")

        # Generate entrypoint.sh
        entrypoint_content = get_entrypoint_sh_content()
        with open(self.output_dir / 'entrypoint.sh', 'w') as f:
            f.write(entrypoint_content)
        vcprint("  ✓ entrypoint.sh - Container startup script", color="light_green")

        vcprint("✅ Docker configuration files generation completed", color="green")

    def _generate_root_files(self):
        """Generate root level files"""
        vcprint("\n📋 STEP 10: Generating root level execution files", color="bright_blue", style="bold")

        settings = self.config.get('settings', {})
        app_name = settings.get('app_name')

        vcprint("  📝 Creating root level execution files...", color="blue")

        migrations_content = get_migrations_content(app_name)
        with open(self.output_dir / 'migrations.py', 'w') as f:
            f.write(migrations_content)
        vcprint("  ✓ migrations.py - Database migration script", color="light_green")

        run_content = get_run_py_content()
        with open(self.output_dir / 'run.py', 'w') as f:
            f.write(run_content)
        vcprint("  ✓ run.py - Application runner script", color="light_green")

        vcprint("✅ Root level files generation completed", color="green")

    def _run_post_create_scripts(self):
        """Run post-creation scripts in the output directory"""
        vcprint("\n📋 STEP 11: Executing post-creation scripts", color="bright_blue", style="bold")

        scripts = self.config.get('post_create_scripts', [])

        if not scripts:
            vcprint("ℹ️  No post-creation scripts configured, skipping this step", color="light_blue")
            return

        vcprint(f"🔧 Found {len(scripts)} post-creation scripts to execute", color="blue")

        # Change to output directory
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
            vcprint(f"\nReturned to original directory: {original_dir}", color="blue")


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

if __name__ == '__main__':
    MicroserviceGenerator(config_path=r"D:\work\matrx\matrx-dream-service\temp\base_config-backup.json",
                          output_dir=r"D:\work\matrx\generated\matrx-scraper-2222").generate_microservice()
