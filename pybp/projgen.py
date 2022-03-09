import os
import pathlib
import datetime

from typing import Optional

import template


_ROOT = pathlib.Path(__file__).parent.parent
_CWD = pathlib.Path.cwd()
_USER_CONFIG_PATH = pathlib.Path.home() / ".config" / "pybp.conf"
_LICENSES_DIR = _ROOT / "licenses"
_GITIGNORE_DIR = _ROOT / "gitignore"

_STATIC_TEMPLATE_VARS = {"year": str(datetime.datetime.today().year)}
# special characters for colored terminal output
_COLOR_START = "\033[94m"
_COLOR_END = "\033[0m"


class _PersistantUserConfig:
    _cached = None

    author: str
    venv_cmd: str

    @classmethod
    def get_dict(cls):
        if cls._cached is not None:
            return cls._cached

        # ask user to fill out config profile first time running
        if not _USER_CONFIG_PATH.exists():
            cls._cached = cls._first_time_init()
            return cls._cached

        with open(_USER_CONFIG_PATH, "r") as f:
            lines = f.readlines()
        d = dict()
        for line in lines:
            k, v = line.split("=")
            d[k.strip()] = v.strip()

        # if this class gets updated we might need to fill in new values
        if len(d) < len(cls.__annotations__):
            cls._cached = cls._first_time_init(d)
            return cls._cached

        cls._cached = d
        return cls._cached

    @classmethod
    def _first_time_init(cls, existing=None):
        if not existing:
            existing = {}
        # if existing dict has been passed in we will use existing values
        # as the defaults. This happens if this data structure gets more fields
        # added to it
        values = {
            k: _user_input(f"CONFIG -- {k}", existing.get(k, None))
            for k in cls.__annotations__
        }
        with open(_USER_CONFIG_PATH, "w") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")
        return values


def _user_input(prompt, default=None):
    if default is not None:
        raw = input(f"{_COLOR_START}{prompt}: ({default}) {_COLOR_END}")
    else:
        raw = input(f"{_COLOR_START}{prompt}: {_COLOR_END}")
    cleaned = raw.strip()
    return cleaned if cleaned else default


def _bool_input(question, default="n"):
    response = _user_input(f"{question} y/n", default)
    if response in ("y", "yes"):
        return True
    return False


def _choice_from_directory(prompt, directory, default="None"):
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


class BaseProjectPlan:
    name: str
    desc: str
    tests: bool
    root: pathlib.Path
    license: Optional[pathlib.Path]
    gitignore: Optional[pathlib.Path]

    def __init__(
        self, name=None, desc=None, tests=None, license=None, gitignore=None
    ):
        self.template_injections = {
            **_STATIC_TEMPLATE_VARS,
            **_PersistantUserConfig.get_dict(),
        }

        if name is None:
            self.name = _user_input("Enter a name for this project", _CWD.name)
        else:
            self.name = name

        if desc is None:
            self.desc = _user_input("Enter a short description")
        else:
            self.desc = desc

        new_dir = _bool_input("Create project in a new directory?")
        self.root = _CWD / self.name if new_dir else _CWD
        self.tests = _bool_input("Add a tests directory?")

        if license is None:
            self.license = _choice_from_directory(
                "Which license would you like to use?", _LICENSES_DIR
            )
        else:
            self.license = None

        if gitignore is None:
            self.gitignore = _choice_from_directory(
                "Which gitignore would you like to use?", _GITIGNORE_DIR
            )
        else:
            self.gitignore = gitignore

    def execute(self):
        self._write_dirs()
        self._write_readme()
        self._write_license()
        self._write_gitignore()

    def _write_dirs(self):
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

        (self.root / self.name).mkdir()

        if self.tests:
            (self.root / "tests").mkdir()

    def _write_readme(self):
        with open(self.root / "README.md", "w") as f:
            f.write(f"# {self.name}\n\n### {self.desc}\n")

    def _write_license(self):
        if not self.license:
            return
        with open(self.license, "r") as f:
            license_text = f.read()
        with open(self.root / self.license_name, "w") as f:
            f.write(template.inject(license_text, self.template_injections))

    def _write_gitignore(self):
        if not self.gitignore:
            return
        with open(self.gitignore, "r") as f:
            gitignore_text = f.read()
        with open(self.root / ".gitignore", "w") as f:
            f.write(gitignore_text)

    @property
    def license_name(self):
        return "COPYING" if self.license.name.lower() == "gpl" else "LICENSE"

    @property
    def license_identifier(self):
        cleaned = self.license.name.lower()
        if cleaned == "gpl":
            return "GPL-3.0-or-later"
        if cleaned == "mit":
            return "MIT"


class PyProject:
    def __init__(self):
        self.base = BaseProjectPlan(gitignore=_GITIGNORE_DIR / "python")
        self.include_dirs = []
        self.project_deps = []
        self.devonly_deps = []
        self.console_scripts = []
        self.packages = [self.base.name]
        self.make_venv = False

    def setup_prompts(self):
        self.make_venv = _bool_input("Make a virtual environment?")

        project_deps = _user_input(
            "Add python package dependencies (space separated)"
        )
        if project_deps:
            self.project_deps.extend(project_deps.split())

        devonly_deps = _user_input(
            "Add dev-only dependencies (space separated)"
        )
        if devonly_deps:
            self.devonly_deps.extend(devonly_deps.split())

    def execute(self):
        self.base.execute()
        self._write_package_init_files()
        self._write_setup_py()
        self._write_setup_cfg()
        self._write_manifest()
        self._handle_venv()

    def _write_package_init_files(self):
        (self.base.root / self.base.name / "__init__.py").touch()
        if self.base.tests:
            (self.base.root / "tests" / "__init__.py").touch()

    def _write_setup_py(self):
        with open(self.base.root / "setup.py", "w") as f:
            f.write(
                'import setuptools\n\nif __name__ == "__main__":\n'
                "    setuptools.setup()"
            )

    def _write_setup_cfg(self):
        usrcfg = _PersistantUserConfig.get_dict()
        lines = [
            "[metadata]",
            f"name = {self.base.name}",
            f"author = {usrcfg['author']}",
            "version = 0.0.1",
            f"description = {self.base.desc}",
            "long_description = file: README.md",
            'long_description_content_type = "text/markdown"',
        ]

        if self.base.license:
            lines.append(f"license = {self.base.license_identifier}")
            lines.append(f"license_file = {self.base.license_name}")

        options = ["[options]", "packages ="]
        for entry in self.packages:
            options.append(f"    {entry}")
        if self.project_deps:
            options.append("install_requires =")
            for entry in self.project_deps:
                options.append(f"    {entry}")
        lines.append("")
        lines.extend(options)

        if self.devonly_deps:
            lines.extend(("", "[options.extras_require]", "dev ="))
            for entry in self.devonly_deps:
                lines.append(f"    {entry}")

        if self.console_scripts:
            lines.extend(("", "[options.entry_points]", "console_scripts ="))
            for entry in self.console_scripts:
                lines.append(f"    {entry}")

        with open(self.base.root / "setup.cfg", "w") as f:
            f.write("\n".join(lines))

    def _write_manifest(self):
        if not self.include_dirs:
            return
        with open(self.base.root / "MANIFEST.in", "w") as f:
            for d in self.include_dirs:
                f.write(f"recursive-include {d} *\n")

    def _handle_venv(self):
        if not self.make_venv:
            return

        commands = [
            f"cd {self.base.root}",
            _PersistantUserConfig().get_dict()["venv_cmd"],
            ". venv/bin/activate",
        ]
        if self.project_deps:
            commands.append("python3 -m pip install .")
        if self.devonly_deps:
            commands.append('python3 -m pip install ".[dev]"')

        os.system(" && ".join(commands))
