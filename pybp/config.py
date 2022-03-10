import pathlib

from . import prompt


_USER_CONFIG_PATH = pathlib.Path.home() / ".config" / "pybp.conf"
CWD = pathlib.Path.cwd()
PYBP_ROOT = pathlib.Path(__file__).parent
TEMPLATE_DIR = PYBP_ROOT / "templates"
LICENSE_DIR = TEMPLATE_DIR / "licenses"
GITIGNORE_DIR = TEMPLATE_DIR / "gitignore"


class PersistantUserConfig:
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
            k: prompt.str_input(f"CONFIG -- {k}", existing.get(k, None))
            for k in cls.__annotations__
        }
        with open(_USER_CONFIG_PATH, "w") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")
        return values
