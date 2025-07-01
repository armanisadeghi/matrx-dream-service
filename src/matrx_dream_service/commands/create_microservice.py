import json
import sys
import os
from cookiecutter.main import cookiecutter
from matrx_utils import vcprint
import importlib.resources as resources
from pathlib import Path


def register_parser(subparsers):
    parser = subparsers.add_parser(
        "create-microservice",
        help="Create a new matrx microservice"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to JSON config file"
    )
    parser.add_argument(
        "--output",
        nargs="?",
        default=".",
        help="Directory to save the generated project"
    )


def run(args):
    config_path = args.config
    output_path = args.output

    vcprint(output_path, color="blue")

    if not os.path.exists(config_path):
        vcprint(f"Error: Config file not found at {config_path}", color="red")
        sys.exit(1)

    with open(config_path, "r") as f:
        config_data = json.load(f)

    default_context = config_data.get("default_context", {})

    try:
        with resources.as_file(resources.files("matrx_dream_service.templates.microservice")) as template_path:
            cookiecutter(
                str(template_path),
                no_input=True,
                extra_context=default_context,
                output_dir=os.path.abspath(output_path)
            )

    except Exception as e:
        vcprint(f"COOKIECUTTER ERROR: {e}", color="red")
        sys.exit(1)
