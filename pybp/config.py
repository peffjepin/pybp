import pathlib
import shutil

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
    def get_dict(cls) -> dict:
        if cls._cached is not None:
            return cls._cached

        # ask user to fill out config profile first time running
        if not _USER_CONFIG_PATH.exists():
            return cls.configure()

        d = cls._read_config()

        # if this class gets updated we might need to fill in new values
        if len(d) < len(cls.__annotations__):
            return cls.configure()

        cls._cached = d
        return d

    @classmethod
    def configure(cls) -> dict:
        if not _USER_CONFIG_PATH.exists():
            shutil.copy(TEMPLATE_DIR / "pybp.conf", _USER_CONFIG_PATH)
        existing = cls._read_config()
        values = {
            k: prompt.str_input(f"PERSISTANT CONFIG -- {k}", existing.get(k, None))
            for k in cls.__annotations__
        }
        with open(_USER_CONFIG_PATH, "w") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")
        cls._cached = values
        return values

    @classmethod
    def _read_config(cls) -> dict:
        with open(_USER_CONFIG_PATH, "r") as f:
            lines = f.readlines()
        d = dict()
        for ln in map(lambda l: l.strip(), lines):
            if not ln:
                continue
            k, v = ln.split("=")
            d[k.strip()] = v.strip()
        return d
