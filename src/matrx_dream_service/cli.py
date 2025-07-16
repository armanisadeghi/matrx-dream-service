import argparse
import json
from .matrx_microservice.generator import MicroserviceGenerator


def create_microservice(args):
    """Create microservice from config"""
    github_access = None
    if args.github_access_file:
        with open(args.github_access_file, 'r') as f:
            github_access = json.load(f)

    generator = MicroserviceGenerator(
        config_path=args.config,
        output_dir=args.output_dir,
        create_github_repo=args.create_github_repo,
        github_project_name=args.github_project_name,
        github_access=github_access,
        github_project_description=args.github_project_description,
        debug=args.debug
    )
    generator.generate_microservice()


def main():
    parser = argparse.ArgumentParser(
        prog='matrx',
        description='MATRX CLI Tool - A utility for managing matrx services and more',
        epilog='For more help, visit the documentation or use matrx <command> --help'
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')  # Added version flag
    parser.add_argument('--debug', action='store_true', help='Enable debug mode globally')  # Global debug

    subparsers = parser.add_subparsers(dest='command', help='Available commands',
                                       required=True)  # Made command required

    # Create microservice command
    create_parser = subparsers.add_parser('create-microservice', help='Create a new microservice project')
    create_parser.add_argument('--config', required=True, help='Path to config JSON file')
    create_parser.add_argument('--output_dir', required=True, help='Output directory for generated microservice')
    create_parser.add_argument('--create_github_repo', action='store_true', help='Create and push to GitHub repo')
    create_parser.add_argument('--github_project_name', type=str,
                               help='Base name for GitHub project (required if creating repo)')
    create_parser.add_argument('--github_project_description', type=str, default='',
                               help='Description for GitHub project')
    create_parser.add_argument('--github_access_file', type=str, help='Path to JSON file for GitHub access/permissions')
    create_parser.add_argument('--debug', action='store_true',
                               help='Enable debug mode for this command')  # Command-specific debug

    # Placeholder for future commands (commented out for now, but structure ready)
    # Example: add_parser = subparsers.add_parser('other-command', help='Description of other command')
    # add_parser.add_argument('--arg1', help='Arg for other command')

    args = parser.parse_args()

    if args.command == 'create-microservice':
        # Handle required fields for GitHub
        if args.create_github_repo and not args.github_project_name:
            create_parser.error('--github_project_name is required when --create_github_repo is set')
        create_microservice(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()