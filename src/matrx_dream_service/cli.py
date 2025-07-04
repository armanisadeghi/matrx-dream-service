import argparse
from .matrx_microservice.generator import MicroserviceGenerator


def create_microservice(config_path: str, output_dir: str):
    """Create microservice from config"""
    generator = MicroserviceGenerator(config_path, output_dir)
    generator.generate_microservice()


def main():
    parser = argparse.ArgumentParser(description='MATRX CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create microservice command
    create_parser = subparsers.add_parser('create-microservice', help='Create a new microservice')
    create_parser.add_argument('--config', required=True, help='Path to config JSON file')
    create_parser.add_argument('--output_dir', required=True, help='Output directory for generated microservice')

    args = parser.parse_args()

    if args.command == 'create-microservice':
        create_microservice(args.config, args.output_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()