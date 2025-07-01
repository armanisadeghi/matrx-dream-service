import argparse
from matrx_dream_service import create_microservice


def main():
    parser = argparse.ArgumentParser(
        prog="matrx-dream-service",
        description="MATRX Dream Service"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: create-microservice
    create_microservice.register_parser(subparsers)

    args = parser.parse_args()

    if args.command == "create-microservice":
        create_microservice.run(args)
    else:
        parser.print_help()
