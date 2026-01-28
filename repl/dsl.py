import logging
import random
from pathlib import Path
from string import Template
from typing import Annotated, Any

import typer
from datasworn.core.models import BaseModel
from pysworn.common import datasworn_tree
from pysworn.renderables import RENDERABLE_TYPES, get_renderable
from pysworn.repl.utils import depth_first_merge, get_chain_map, get_id_dict
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import Pretty
from rich.rule import Rule
from rich.traceback import install
from rich.tree import Tree

console = Console(force_terminal=True)
install()

logging.getLogger("markdown_it").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

app = typer.Typer(
    no_args_is_help=True,
    invoke_without_command=True,
)

# Global state
state: dict[str, Any] = {
    "chain": [],
    "id_dict": {},
    "index": datasworn_tree.index,
}


# class Collection(UserDict):
#     def __init__(self, name: str, ruleset: str):
#         self.id = f"collection:{ruleset}/{name}"

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
    d = state["id_dict"]
    d = depth_first_merge(*[d[k] for k in d])
    for k in args:
        if k in d:
            d = d[k]
        else:
            log.error(f"Unknown object {k}. Did you mean:")
            print(" ".join(d.keys()))
            return None
    return d


COMMANDS = {
    "view": print_datasworn,
}


def parse_line(line: str) -> tuple[str, list[str], dict[str, str]] | None:
    if not (tokens := line.split()):
        return None
    log.debug(f"Parsing {tokens} from line")
    cmd: str = tokens[0]
    args: list[str] = [k for k in tokens[1:] if "=" not in k]
    kwargs: dict[str, str] = {
        k: v for k, v in (item.split("=") for item in tokens[1:] if "=" in item)
    }
    return cmd, args, kwargs


def parse_dsl(dsl: str):
    for line in dsl.splitlines():
        if "#" in line:
            line = line.split("#")[0]
        if not line:
            continue
        line.strip()
        if not (parsed_line := parse_line(line)):
            continue
        cmd, args, kwargs = parsed_line
        log.debug(f"Parsed '{cmd}' {args} {kwargs}")
        obj = get_object_by_id(args)

        match obj:
            case dict():
                print(" ".join(obj.keys()))
            case list():
                # print_datasworn(obj[0], **kwargs)
                for o in obj[1:]:
                    print(f"See also: {o.id}")

                # target = f"*{obj[0].id.split(':')[1]}*"
                # print(target)
                # keys = fnmatch.filter(list(datasworn_tree.index), target)
                target = obj[0].id.split(":")[1]
                keys = [k for k in datasworn_tree.index if target in k]
                for k in keys:
                    print(Rule(k))
                    print_datasworn(index[k], **kwargs)
                    if state["debug"]:
                        print(Pretty(index[k]))
            case str():
                print(obj)
                if obj in index:
                    print_datasworn(index[obj])
            case None:
                log.error("No object found.")
            case _:
                log.error(f"Unknown object type {type(obj)}")
            # if obj:
            # COMMANDS[cmd](obj, **kwargs)


@app.command()
def load(file_path: Annotated[str, typer.Argument()]):
    lines = Path(file_path).read_text()
    parse_dsl(lines)


@app.command("exec")
def exec_line(line: str):
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
def ids(no_rows: Annotated[bool, typer.Option("-n", "--no-rows")] = False):
    for k in index:
        tag, path = k.split(":")
        if "." in path and no_rows:
            continue
        print(path)
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
def map_(
    type_: Annotated[list[str], typer.Option("-t", "--type")] = ["oracle_rollable"],
    print_: Annotated[bool, typer.Option("-p", "--print")] = False,
):
    chain = state["chain"]

    nd = state["id_dict"]
    # print(nd)

    # cm = get_chain_map(*[nd[k] for k in nd])
    # print(cm)

    cm = depth_first_merge(*[nd[k] for k in nd])
    print(cm)
    return

    def _expand(
        d: dict[str, Any],
        node,
        path: str = "",
    ):
        for k, v in d.items():
            path_ = f"{path} {k}"
            print(path_)
            if isinstance(v, Template):
                d[k] = []
                for c in chain:
                    id_ = v.substitute(ruleset=c)
                    obj = index.get(id_, None)
                    if obj:
                        d[k].append(c)
                        if print_:
                            console.print(get_renderable(obj))
                node.add(f"{k} [blue]{', '.join(d[k])}")
            else:
                node_ = node.add(f"{k}")
                _expand(v, node=node_, path=path_)

    tree = Tree(str(chain), guide_style="green")
    _expand(id_dict, node=tree)

    for t in type_:
        print(id_dict[t])

    print(tree)


@app.callback()
def main(
    chain: Annotated[list[str], typer.Option("-c", "--chain")] = [
        # "starsmith", "starforged",
        # "lodestar",
        "delve",
        "classic",
    ],
    log_level: Annotated[
        str, typer.Option("-l", "--log-level", case_sensitive=False)
    ] = "info",
    debug: Annotated[bool, typer.Option("-d", "--debug")] = False,
):
    state["debug"] = debug

    logging.basicConfig(
        level=log_level.upper(),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )

    # useful chains:
    # classic delve lodestar
    # starforged sundered_isles ancient_wonders

    state["chain"] = chain
    maps = [datasworn_tree[c] for c in chain]
    state["id_dict"] = get_id_dict(*maps)
    return

    def _expand(d: dict[str, Any]):
        for k, v in d.items():
            if isinstance(v, Template):
                d[k] = []
                for c in chain:
                    id_ = v.substitute(ruleset=c)
                    obj = index.get(id_, None)
                    if obj:
                        d[k].append(obj)
            else:
                _expand(v)

    _expand(state["id_dict"])


if __name__ == "__main__":
    app()
