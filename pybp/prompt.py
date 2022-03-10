import pathlib

from typing import Optional

# special characters for colored terminal output
_COLOR_START = "\033[94m"
_COLOR_END = "\033[0m"


def str_input(prompt: str, default: str = None) -> str:
    if default is not None:
        raw = input(f"{_COLOR_START}{prompt}: ({default}) {_COLOR_END}")
    else:
        raw = input(f"{_COLOR_START}{prompt}: {_COLOR_END}")
    cleaned = raw.strip()
    return cleaned if cleaned else default


def bool_input(question: str, default: str = "n") -> bool:
    response = str_input(f"{question} y/n", default)
    if response in ("y", "yes"):
        return True
    return False


def choice_from_directory(
    prompt: str, directory: pathlib.Path, default: pathlib.Path = "None"
) -> Optional[pathlib.Path]:
    # gather input from the user
    print(f"{_COLOR_START}{prompt}: ({default}){_COLOR_END}")
    names = [p.name for p in directory.iterdir()]
    for i, name in enumerate(names):
        print(f"({i}): {name}")
    response = input().strip()

    # no response means they went with the default "None"
    if not response:
        return None

    # parse response, could be a number or a name
    else:
        try:
            # if response is given as a number find the corresponding file
            n = int(response)
            return directory / names[n]
        except ValueError:
            # name given plainly... it must actually be a file
            path = directory / response
            assert path.exists()
            return path
