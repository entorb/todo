"""Read pyproject.toml, write requirements.txt for pip install on webserver."""

import tomllib
from pathlib import Path

p_in = Path(__file__).parent.parent / "pyproject.toml"
p_out = Path(__file__).parent.parent / "requirements.txt"

with p_in.open("rb") as fh:
    deps = sorted(tomllib.load(fh)["project"]["dependencies"], key=str.casefold)
    deps = [x.replace("~=", ">=") for x in deps]

p_out.write_text(
    "# created by gen_requirements.py from pyproject.toml\n" + "\n".join(deps) + "\n"
)
