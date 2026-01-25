import fnmatch
import logging
import random
from calendar import c
from collections import ChainMap, UserDict
from collections.abc import Mapping
from encodings.punycode import T
from string import Template
from typing import Any, Generic
from webbrowser import get

import typer
from datasworn.core.models import BaseModel
from pysworn.common import datasworn_tree
from pysworn.renderables import RENDERABLE_TYPES, get_renderable
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.traceback import install

console = Console(force_terminal=True)
install()

app = typer.Typer(no_args_is_help=True, invoke_without_command=True)

# classic = datasworn_tree["classic"]
# classic = datasworn_tree["delve"]
# datasworn_tree["starforged"]

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)
logging.getLogger("markdown_it").setLevel(logging.WARNING)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Collection(UserDict):
    def __init__(self, name: str, ruleset: str):
        self.id = f"collection:{ruleset}/{name}"


# for ruleset in datasworn_tree:
#     for k, v in vars(datasworn_tree[ruleset]).items():
#         if isinstance(v, dict):
#             c = Collection(k, ruleset)

# setattr(datasworn_tree[ruleset], k, c)
# datasworn_tree.index[c.id] = c


index = datasworn_tree.index


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


def basemodel_getitem(self, key) -> Any:
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


def get_nested_dict(index: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for _id in index:
        if ":" not in _id or "." in _id.split(":")[1]:
            continue
        *nodes, last = (_id.split(":")[1]).split("/")
        d = result
        for k in nodes:
            d = d.setdefault(k, {})
        d[last] = {}
    return result


# def print_nested_dict(d: dict[str, Any], level: int = 0) -> None:
# for k in d:
#     print(f"{' ' * level}{k}")
#     print_nested_dict(d[k], level + 2)


def print_nested_dict(d: dict[str, Any], path: str = "") -> None:
    for k in d:
        if d[k]:
            print_nested_dict(d[k], f"{path} {k}")
        else:
            print(f"{path} {k}")
        # print_nested_dict(d[k], f"{path} {k}")


def print_datasworn(obj: BaseModel, *args: Any, **kwargs: Any) -> None:
    # renderable = RENDERABLE_TYPES.get(type(obj))
    # if renderable:
    #     print(Panel(renderable(obj, **kwargs), width=120))
    # else:
    #     print(f"No renderable found for {type(obj)}")
    print(get_renderable(obj, *args, **kwargs))


def roll_oracle_collection(oracle_collection, name):
    for title, oracle in oracle_collection[name].contents.items():
        row = random.choice(oracle.rows)
        print(f"{title.upper()}:")
        print_datasworn(row)


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

    co = classic.oracles
    print(list(co))

    for coll in classic.oracles:
        print(f"--- {coll.title()} ---")
        roll_oracle_collection(classic.oracles, coll)


def move():
    classic = datasworn_tree["classic"]
    adventure = classic.moves["adventure"]
    face_danger = adventure.contents["face_danger"]

    print(face_danger.outcomes.strong_hit)

    print_datasworn(face_danger)


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


def get_object_by_id(args: list[str]) -> BaseModel | None:
    target = f"*{'*'.join(args)}"
    keys = fnmatch.filter(list(datasworn_tree.index), target)
    if not keys:
        log.error(f"Unknown object {target}. Did you mean:")
        target = f"*{'*'.join(args)}*"
        matches = fnmatch.filter(list(datasworn_tree.index), target)
        matches = set(k for k in matches if "." not in k)
        print_nested_dict(get_nested_dict(matches))
        return None
    if len(keys) > 1:
        print(keys)
        print("Multiple choices. Did you mean:")
        print_nested_dict(get_nested_dict(keys))
        return None
    return index.get(keys[0], None)


COMMANDS = {
    "view": print_datasworn,
}


def parse_dsl(dsl: str):
    for line in dsl.splitlines():
        if line.strip().startswith("#"):
            continue
        parsed_line = parse_line(line.lower())
        if not parsed_line:
            continue
        cmd, args, kwargs = parsed_line

        obj = get_object_by_id(args)
        if obj:
            COMMANDS[cmd](obj, **kwargs)

        # print_datasworn(obj)


@app.command()
def main(args: list[str]):
    dsl = """
view classic hinterlands
view classic old_world
view classic face_danger
view classic face_danger outcome=strong_hit
view classic character role
view delve journal
view classic character role
    """
    line = " ".join(args)
    parse_dsl(line)


@app.command()
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


@app.command()
def ids():
    for k in index:
        print(k)

    return

    for k, v in index.items():
        # print(k, v.__class__)
        if ":" not in k:
            print(k)
            continue
        tag, path = k.split(":")
        if "." in path:
            continue
        if "." in tag:
            tag = tag.split(".")[0]
        if tag == "oracle_rollable":
            tag = "oracle"
        if "_" in tag:
            continue
        path = path.split("/")
        path.insert(1, tag)

        print(" ".join(path))


@app.command()
def show_tree():
    for k in datasworn_tree:
        print(datasworn_tree[k])


@app.command("map")
def map_():
    merged_dict = get_merged_dict()
    print(merged_dict)

    def _print_recursive(d: dict[str, Any], path: str = ""):
        for k, v in d.items():
            path_ = f"{path} {k}"
            print(path_)
            if isinstance(v, Template):
                for c in chain:
                    id_ = v.substitute(ruleset=c)
                    obj = index.get(id_, None)
                    if obj:
                        console.print(get_renderable(obj))
            else:
                _print_recursive(v, path_)

    _print_recursive(merged_dict)


if __name__ == "__main__":
    # datasworn_tree["classic"]
    # datasworn_tree["delve"]
    datasworn_tree["starforged"]
    datasworn_tree["sundered_isles"]
    datasworn_tree["ancient_wonders"]

    # for k in datasworn_tree:
    #     datasworn_tree[k]

    app()
