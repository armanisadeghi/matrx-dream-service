# {{cookiecutter.app_dirname}}/migrations.py

import database.db_conf
from matrx_utils import clear_terminal, vcprint, settings
from matrx_orm.schema_builder import SchemaManager
from matrx_orm.schema_builder.helpers.git_checker import check_git_status



clear_terminal()

ADMIN_SAVE_DIRECT_ROOT = settings.ADMIN_SAVE_DIRECT_ROOT
ADMIN_PYTHON_ROOT = settings.ADMIN_PYTHON_ROOT
ADMIN_TS_ROOT = settings.ADMIN_TS_ROOT


schema = "public"
database_project = "{{cookiecutter.app_name}}" # Your app name
additional_schemas = ["auth"]
save_direct = ADMIN_SAVE_DIRECT_ROOT

if save_direct:
    check_git_status(save_direct)
    vcprint(
        "\n[MATRX AUTOMATED SCHEMA GENERATOR] WARNING!! save_direct is True. Proceed with caution.\n",
        color="red",
    )
    input("WARNING: This will overwrite the existing schema files. Press Enter to continue...")

schema_manager = SchemaManager(
    schema=schema,
    database_project=database_project,
    additional_schemas=additional_schemas,
    save_direct=save_direct,
)
schema_manager.initialize()


matrx_schema_entry = schema_manager.schema.generate_schema_files()

matrx_models = schema_manager.schema.generate_models()

analysis = schema_manager.analyze_schema()
vcprint(
    data=analysis,
    title="Schema Analysis",
    pretty=True,
    verbose=False,
    color="yellow",
)

schema_manager.schema.code_handler.print_all_batched()