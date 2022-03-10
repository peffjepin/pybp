import os
import pathlib

from typing import Optional

from . import template
from . import prompt
from . import config


class BaseProjectPlan:
    name: str
    desc: str
    tests: bool
    root: pathlib.Path
    license: Optional[pathlib.Path]
    gitignore: Optional[pathlib.Path]

    def __init__(
        self,
        name=None,
        desc=None,
        tests=None,
        license=None,
        gitignore=None,
        root=None,
    ):
        self.name = name
        self.desc = desc
        self.tests = tests
        self.license = license
        self.gitignore = gitignore
        self.root = root

    def setup_prompts(self):
        new_dir = prompt.bool_input("Create project in a new directory?")
        if self.name is None:
            self.name = prompt.str_input(
                "Enter a name for this project", config.CWD.name
            )
        self.root = config.CWD / self.name if new_dir else config.CWD
        if self.desc is None:
            self.desc = prompt.str_input("Enter a short description")
        if self.tests is None:
            self.tests = prompt.bool_input("Add a tests directory?")
        if self.license is None:
            self.license = prompt.choice_from_directory(
                "Which license would you like to use?", config.LICENSE_DIR
            )
        if self.gitignore is None:
            self.gitignore = prompt.choice_from_directory(
                "Which gitignore would you like to use?", config.GITIGNORE_DIR
            )

    def execute(self):
        if self.root is None:
            self.setup_prompts()
        self._write_dirs()
        self._write_readme()
        self._write_license()
        self._write_gitignore()

    @property
    def namespace(self):
        return {"plan": self}

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
        template.copy(
            self.license, self.root / self.license_name, self.namespace
        )

    def _write_gitignore(self):
        if not self.gitignore:
            return
        template.copy(self.gitignore, self.root / ".gitignore", self.namespace)


class PyProject(BaseProjectPlan):
    _TEMPLATE_DIR = config.TEMPLATE_DIR / "python"

    def __init__(self):
        super().__init__(gitignore=config.GITIGNORE_DIR / "python")
        self.include_dirs = []
        self.project_deps = []
        self.devonly_deps = []
        self.console_scripts = []
        self.packages = []
        self.make_venv = False

    def setup_prompts(self):
        super().setup_prompts()
        self.make_venv = prompt.bool_input("Make a virtual environment?")
        project_deps = prompt.str_input(
            "Add python package dependencies (space separated)"
        )
        if project_deps:
            self.project_deps.extend(project_deps.split())
        devonly_deps = prompt.str_input(
            "Add dev-only dependencies (space separated)"
        )
        if devonly_deps:
            self.devonly_deps.extend(devonly_deps.split())

    def execute(self):
        super().execute()
        self.packages.append(self.name)
        self._write_package_init_files()
        self._write_setup_py()
        self._write_setup_cfg()
        self._write_manifest()
        self._handle_venv()

    def _write_package_init_files(self):
        (self.root / self.name / "__init__.py").touch()
        if self.tests:
            (self.root / "tests" / "__init__.py").touch()

    def _write_setup_py(self):
        template.copy(
            self._TEMPLATE_DIR / "setup.py",
            self.root / "setup.py",
            {"plan": self},
        )

    def _write_setup_cfg(self):
        template.copy(
            self._TEMPLATE_DIR / "setup.cfg",
            self.root / "setup.cfg",
            {"plan": self},
        )

    def _write_manifest(self):
        if not self.include_dirs:
            return
        with open(self.root / "MANIFEST.in", "w") as f:
            for d in self.include_dirs:
                f.write(f"recursive-include {d} *\n")

    def _handle_venv(self):
        if not self.make_venv:
            return

        commands = [
            f"cd {self.root}",
            config.PersistantUserConfig().get_dict()["venv_cmd"],
            ". venv/bin/activate",
        ]
        if self.project_deps:
            commands.append("python3 -m pip install .")
        if self.devonly_deps:
            commands.append('python3 -m pip install ".[dev]"')

        os.system(" && ".join(commands))
