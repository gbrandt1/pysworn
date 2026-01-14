import logging
import random
import re
from calendar import c
from tkinter import E
from typing import Any

from datasworn.core import datasworn_tree, index
from datasworn.core.models import BaseModel
from pysworn.renderables import RENDERABLE_TYPES

# from pydantic import BaseModel
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.traceback import install

console = Console(force_terminal=True)
install()
# for k in datasworn_tree:
#     datasworn_tree[k]
# classic = datasworn_tree["classic"]
# classic = datasworn_tree["delve"]
# datasworn_tree["starforged"]

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)
log = logging.getLogger(__name__)
logging.getLogger("markdown_it").setLevel(logging.WARNING)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def basemodel_getattr(self, name):
    try:
        contents = object.__getattribute__(self, "contents")
        if name in contents:
            return contents[name]
        else:
            raise AttributeError
    except AttributeError:
        pass
    try:
        collections = object.__getattribute__(self, "collections")
        if name in collections:
            return collections[name]
        else:
            raise AttributeError
    except AttributeError:
        pass
    return object.__getattribute__(self, name)


setattr(BaseModel, "__getattr__", basemodel_getattr)


def basemodel_getitem(self, key):
    try:
        return self.contents[key]
    except Exception:
        pass
    try:
        return self.collections[key]
    except Exception:
        pass
    raise KeyError


setattr(BaseModel, "__getitem__", basemodel_getitem)


def print_datasworn(obj: BaseModel, *args: Any, **kwargs: Any) -> None:
    renderable = RENDERABLE_TYPES.get(type(obj))
    if renderable:
        print(Panel(renderable(obj), width=120))
    else:
        print(f"No renderable found for {type(obj)}")


def start_campaign():
    classic = datasworn_tree["classic"]

    ironlands = classic.atlas["ironlands"]

    region = random.choice(list(ironlands.contents))
    print(f"Region: {region.upper()}")
    print_datasworn(ironlands[region])

    for truth in classic.truths:
        print(f"{truth.upper()}")
        option = random.choice(classic.truths[truth].options)
        print_datasworn(option)

    asset_ids = [i for i in index if i.startswith("asset:")]

    for asset_id in random.sample(asset_ids, 3):
        print_datasworn(index[asset_id])

    # return

    co = classic.oracles

    print(list(co))

    def roll_oracle_collection(oracle_collection, name):
        for title, oracle in oracle_collection[name].contents.items():
            row = random.choice(oracle.rows)
            print(f"{title.upper()}:")
            print_datasworn(row)

    for coll in classic.oracles:
        print(f"--- {coll.title()} ---")
        roll_oracle_collection(classic.oracles, coll)


COMMANDS = {
    "VIEW": print_datasworn,
}


def parse_line(line) -> tuple[str, list[str], dict[str, str]] | None:
    if not (tokens := line.split()):
        return
    log.debug(f"Parsing {tokens} from line")
    cmd: str = tokens[0]
    args: list[str] = [k for k in tokens[1:] if "=" not in k]
    kwargs: dict[str, str] = {
        k: v for k, v in (item.split("=") for item in tokens[1:] if "=" in item)
    }
    return cmd, args, kwargs


def get_object(args: list[str]) -> BaseModel | dict[str, Any] | str:
    obj = datasworn_tree[args[0]]
    for arg in args[1:]:
        # print(obj)
        log.debug(f"Looking for '{arg}' on {type(obj)}")
        match obj:
            case BaseModel():
                obj_ = getattr(obj, arg, None)
                log.debug(type(obj_))
                if obj_:
                    log.debug(f"Found '{arg}' field on {type(obj)}")
                else:
                    if arg in list(getattr(obj, "contents")):
                        log.debug(f"Found {arg} in contents on {type(obj)}")
                        obj_ = obj.contents[arg]
                    elif arg in list(getattr(obj, "collections")):
                        log.debug(f"Found {arg} in collections on {type(obj)}")
                        obj_ = obj.collections[arg]
                    else:
                        msg = f"Unknown field {arg} on {type(obj)}"
                        raise Exception(msg)
                obj = obj_
            case dict():
                log.debug(f"Found '{arg}' dict key on {type(obj)}")
                obj = obj[arg]

            case _:
                raise Exception(f"Unknown type {type(obj)}")

    print(f"{type(obj)}")
    return obj


def parse_dsl(dsl: str):
    for line in dsl.splitlines():
        if line.strip().startswith("#"):
            continue
        parsed_line = parse_line(line)
        if not parsed_line:
            continue
        cmd, args, kwargs = parsed_line

        obj = get_object(args)
        # COMMANDS[cmd](*args, **kwargs)

        print_datasworn(obj)


def main():
    dsl = """
    VIEW classic atlas
    VIEW classic truths old_world
    VIEW classic moves adventure face_danger
    """
    parse_dsl(dsl)


def ids():
    for k, v in index.items():
        print(k, v.__class__)


def render_ids():
    from rich.table import Table

    t = Table()
    parents: set[tuple[type, type]] = set()
    for k, v in index.items():
        if ".row:" in k:
            continue
        r_type = None
        renderable = None
        for r_type in RENDERABLE_TYPES:
            if isinstance(v, r_type):
                renderable = RENDERABLE_TYPES[r_type]
                break

        parent = type(v).__mro__[1]
        if not renderable:
            if parent is not BaseModel:
                t.add_row(f"{k}", f"{parent}", f"{renderable}", f"{type(v)}")
                parents.add((parent, type(v)))
        else:
            # console.print(f"{k}: {type(v)} ({parent}) --> {r_type} {renderable}")
            console.print(
                Panel(
                    renderable(v),
                    # width=120,
                )
            )
    print(t)
    if parents:
        print(parents)


if __name__ == "__main__":
    # print(RENDERABLE_TYPES)
    # render_ids()
    # ids()

    start_campaign()
