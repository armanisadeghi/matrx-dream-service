import argparse
import os
import sys
import json
from cookiecutter.main import cookiecutter

def main():
    parser = argparse.ArgumentParser(
        prog="matrx-microservice",
        description="Generate a new microservice project from config"
    )

    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="Create a new service")
    create_parser.add_argument("template", help="The template directory (usually 'project_template')")
    create_parser.add_argument("--config", required=True, help="Path to JSON config file")
    create_parser.add_argument("output", nargs="?", default=".", help="Output directory (use '.' for current)")

    args = parser.parse_args()

    if args.command == "create":
        if not os.path.exists(args.config):
            print(f"Error: Config file not found at {args.config}")
            sys.exit(1)

        with open(args.config, "r") as f:
            config_data = json.load(f)

        context = {"cookiecutter": config_data}

        cookiecutter(
            args.template,
            no_input=True,
            extra_context=context,
            output_dir=args.output
        )
    else:
        parser.print_help()
