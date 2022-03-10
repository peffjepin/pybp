import argparse

from . import projgen
from . import config


parser = argparse.ArgumentParser()
commands = parser.add_subparsers(help="commands", dest="command")
configure = commands.add_parser(
    "configure", help="cli prompt to update PersistantUserConfig"
)
pypkg = commands.add_parser(
    "pypkg", help="cli prompts to generate python package boilerplate"
)
args = parser.parse_args()


def main():
    if args.command == "configure":
        config.PersistantUserConfig.configure()
        exit(0)
    elif args.command == "pypkg":
        plan = projgen.PyProject()
        plan.setup_prompts()
        plan.execute()
        exit(0)
