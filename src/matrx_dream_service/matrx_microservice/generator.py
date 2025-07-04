import json
from pathlib import Path
from typing import Dict, Any
import subprocess
import os
import sys

from matrx_utils import vcprint

from matrx_dream_service.matrx_microservice.contents import get_gitignore_content, get_conversions_content, \
    get_validation_content, get_app_py_content, get_settings_content, get_system_logger_content, \
    get_docker_file_content, get_entrypoint_sh_content, get_run_py_content, get_migrations_content


class MicroserviceGenerator:
    def __init__(self, config_path: str, output_dir: str):
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        vcprint("🔧 Loading configuration...", color="cyan", style="bold")
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        vcprint(f"✅ Configuration loaded successfully from: {self.config_path}", color="green")
        return config

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
        self._generate_core_files()
        self._generate_docker_files()
        self._generate_root_files()
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

        app_name = settings.get('app_name', 'microservice')
        app_version = settings.get('app_version', '0.1.0')
        app_description = settings.get('app_description', 'A microservice')
        requires_python = settings.get('requires_python', '>=3.8')
        dependencies = settings.get('dependencies', [])
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

        if additional_content:
            content += f"\n{additional_content}\n"
            vcprint("  ✓ Additional project configuration added", color="light_green")

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

        # Create default schema
        default_schema = {
            "definitions": {
                "MIC_CHECK_DEFINITION": {
                    "mic_check_message": {
                        "REQUIRED": False,
                        "DEFAULT": "Service mic check",
                        "VALIDATION": "validate_mic_check_min_length",
                        "DATA_TYPE": "string",
                        "CONVERSION": "convert_mic_check",
                        "REFERENCE": None,
                        "COMPONENT": "input",
                        "COMPONENT_PROPS": {},
                        "DESCRIPTION": f"Test message for {app_primary_service_name} service connectivity",
                        "ICON_NAME": "Mic"
                    }
                }
            },
            "tasks": {
                f"{app_primary_service_name.upper()}_SERVICE": {
                    "MIC_CHECK": {"$ref": "definitions/MIC_CHECK_DEFINITION"}
                }
            }
        }

        # Merge user schema with default
        merged_schema = default_schema.copy()

        # Merge definitions
        if "definitions" in user_schema:
            vcprint(f"  📝 Merging {len(user_schema['definitions'])} custom definitions", color="blue")
            merged_schema["definitions"].update(user_schema["definitions"])

        # Merge tasks
        if "tasks" in user_schema:
            vcprint(f"  🔧 Merging {len(user_schema['tasks'])} custom task services", color="blue")
            for service_name, tasks in user_schema["tasks"].items():
                if service_name in merged_schema["tasks"]:
                    merged_schema["tasks"][service_name].update(tasks)
                else:
                    merged_schema["tasks"][service_name] = tasks.copy()

        # Ensure MIC_CHECK exists in all services
        for service_name in merged_schema["tasks"]:
            if "MIC_CHECK" not in merged_schema["tasks"][service_name]:
                merged_schema["tasks"][service_name]["MIC_CHECK"] = {"$ref": "definitions/MIC_CHECK_DEFINITION"}

        vcprint(
            f"  ✓ Schema merged: {len(merged_schema['definitions'])} definitions, {len(merged_schema['tasks'])} services",
            color="light_green")

        # Create app_schema directory and schema.py
        app_schema_dir = self.output_dir / 'app_schema'
        app_schema_dir.mkdir(parents=True, exist_ok=True)
        vcprint("  📁 Created app_schema directory", color="light_green")

        schema_file_path = app_schema_dir / 'schema.py'
        schema_content = f'''from matrx_connect.socket.schema import register_schema

schema = {merged_schema}

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
        vcprint(f"  🔧 Generating {len(merged_schema['tasks'])} service files...", color="blue")
        for service_name, tasks in merged_schema["tasks"].items():
            service_file_name = service_name.lower().replace('_service', '') + '_service.py'
            service_class_name = service_name.lower().replace('_service', '').capitalize() + 'Service'

            vcprint(f"    ⚙️  Generating service: {service_class_name}", color="blue")

            # Collect all field parameters from all tasks
            all_fields = set()
            for task_name, task_def in tasks.items():
                if isinstance(task_def, dict) and "$ref" not in task_def:
                    all_fields.update(task_def.keys())
                elif isinstance(task_def, dict) and "$ref" in task_def:
                    # Resolve reference to get fields
                    ref_path = task_def["$ref"].split("/")
                    if len(ref_path) == 2 and ref_path[0] == "definitions":
                        def_name = ref_path[1]
                        if def_name in merged_schema["definitions"]:
                            all_fields.update(merged_schema["definitions"][def_name].keys())

            # Generate service file content
            service_content = f'''from matrx_connect.socket.core import SocketServiceBase
class {service_class_name}(SocketServiceBase):

    def __init__(self):
        self.stream_handler = None
        self.mic_check_message = None
'''

            # Add all field parameters to init
            for field in sorted(all_fields):
                if field != "mic_check_message":  # Already added above
                    service_content += f'        self.{field} = None\n'

            service_content += f'''
        super().__init__(
            app_name="{app_name}",
            service_name="{service_class_name}",
            log_level="INFO",
            batch_print=False,
        )

    async def process_task(self, task, task_context=None, process=True):
        return await self.execute_task(task, task_context, process)
    '''

            # Generate async methods for each task
            for task_name in tasks.keys():
                method_name = task_name.lower()
                if method_name == "mic_check":
                    # Special handling for mic_check
                    service_content += f'''
    async def {method_name}(self):
        await self.stream_handler.send_chunk(
            "[{service_name} SERVICE] Mic Check Response to: "
            + self.mic_check_message
        )
        await self.stream_handler.send_end()
    '''
                else:
                    service_content += f'''
    async def {method_name}(self):
        # Implement {task_name.lower()} logic here
        pass
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
'''

        # Import all service classes
        for service_name in merged_schema["tasks"].keys():
            service_file_name = service_name.lower().replace('_service', '') + '_service'
            service_class_name = service_name.lower().replace('_service', '').capitalize() + 'Service'
            app_factory_content += f'from .{service_file_name} import {service_class_name}\n'

        app_factory_content += '''

class AppServiceFactory(ServiceFactory):
    def __init__(self):
        super().__init__()
'''

        # Register all services
        for service_name in merged_schema["tasks"].keys():
            service_class_name = service_name.lower().replace('_service', '').capitalize() + 'Service'
            service_key = service_name.lower()
            if service_name == f"{app_primary_service_name.upper()}_SERVICE":
                app_factory_content += f'        self.register_service("default_service", {service_class_name})\n'
            else:
                app_factory_content += f'        self.register_service("{service_key}", {service_class_name})\n'

        app_factory_content += '''
        # Example of registering a single-instance service:
        # self.register_service(service_name="custom_service", service_class=CustomService)

        # Example of registering a multi-instance service:
        # self.register_multi_instance_service(service_name="worker_service", service_class=WorkerService)
    '''

        with open(app_factory_path, 'w') as f:
            f.write(app_factory_content)

        vcprint("  ✓ Service factory (app_factory.py) generated", color="light_green")
        vcprint("✅ Application schema and services generation completed", color="green")

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
                        vcprint(f"❌ Script {i} failed with return code {return_code}: {script}", color="red", style="bold")
                except FileNotFoundError:
                    vcprint(f"❌ Command not found: {script}", color="red")
                except Exception as e:
                    vcprint(f"❌ Error executing script '{script}': {e}", "red")
        finally:
            os.chdir(original_dir)
            vcprint(f"\nReturned to original directory: {original_dir}", color="blue")


if __name__ == '__main__':
    MicroserviceGenerator(config_path=r"D:\work\matrx\matrx-dream-service\temp\base_config.json",
                          output_dir=r"D:\work\matrx\generated\matrx-scraper").generate_microservice()
