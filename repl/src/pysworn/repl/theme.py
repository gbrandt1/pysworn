from pathlib import Path
from typing import Any

from rich.default_styles import DEFAULT_STYLES
from rich.theme import Theme

pysworn_theme_dict: dict[str, Any] = {}

# for k, v in DEFAULT_STYLES.items():
#     # if str(v) != "none":
#     # print(f"{k}: {v}")
#     # vv = str(v).replace("blue", "white")
#     # vv = vv.replace("magenta", "white")
#     # pysworn_theme_dict[k] = vv

#     pysworn_theme_dict |= {
#         "scope.border": "dim",
#         log.path = dim
#     }


pysworn_theme = Theme.read(str(Path(__file__).parent / "theme.cfg"))
