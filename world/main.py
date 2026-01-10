import logging
import random
from inspect import getfullargspec, signature
from typing import Any, TypeAliasType, Union, get_args, get_origin

from datasworn.core import datasworn_tree, index
from pydantic import BaseModel
from pysworn.renderables import (
    MoveRenderable,
)
from rich import print
from rich.logging import RichHandler
from rich.panel import Panel
from rich.traceback import install

install()
classic = datasworn_tree["classic"]

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)
log = logging.getLogger(__name__)
logging.getLogger("markdown_it").setLevel(logging.WARNING)


def find_renderable(obj: object):
    """Find Renderable by matching type annotation with object class."""

    def _match_typealiastype(tat: TypeAliasType) -> type | None:
        arg, *_ = get_args(tat.__value__)
        if get_origin(arg) is Union:
            for union_arg in get_args(arg):
                if isinstance(obj, union_arg):
                    log.debug(f"{obj.__class__} --> {union_arg}")
                    return union_arg
        elif isinstance(obj, arg):
            log.debug(f"{obj.__class__} -->  {arg}")
            return arg
        else:
            log.debug("Class not found")
        return None

    for cls in MoveRenderable.RENDERABLES.values():
        params = signature(cls.__init__).parameters

        fullargspec = getfullargspec(cls.__init__)
        for k, v in fullargspec.annotations.items():
            if isinstance(v, TypeAliasType):
                if _match_typealiastype(v):
                    return cls
            elif isinstance(v, type):
                if isinstance(obj, v):
                    return cls


def print_datasworn(obj: BaseModel, *args: Any, **kwargs: Any) -> None:
    renderable = find_renderable(obj)
    if renderable:
        print(Panel(renderable(obj), width=120))
    else:
        print(f"No renderable found for {type(obj)}")


def start_campaign():
    ironlands = classic.atlas["ironlands"].contents
    region = random.choice(list(ironlands))
    print_datasworn(ironlands[region])

    for truth in classic.truths:
        print(f"{truth.upper()}")
        option = random.choice(classic.truths[truth].options)
        print_datasworn(option)

    asset_ids: list[str] = [i for i in index if i.startswith("asset:")]

    for asset_id in random.sample(asset_ids, 3):
        print_datasworn(index[asset_id])

    co = classic.oracles

    print(list(co))
    print(list(co["name"].contents))

    name = co["name"].contents
    for title, oracle in name.items():
        row = random.choice(oracle.rows)
        print(f"{title.upper()}: {row.text}")

    print(list(co["character"].contents))

    character = co["character"].contents
    for title, oracle in character.items():
        row = random.choice(oracle.rows)
        print(f"{title.upper()}: {row.text}")

    print(list(co["place"].contents))

    place = co["place"].contents
    for title, oracle in place.items():
        row = random.choice(oracle.rows)
        print(f"{title.upper()}: {row.text}")

    print(list(co["turning_point"].contents))

    turning_point = co["turning_point"].contents
    for title, oracle in turning_point.items():
        row = random.choice(oracle.rows)
        print(f"{title.upper()}: {row.text}")

    print(list(co["turning_point"].contents))


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


if __name__ == "__main__":
    main()
