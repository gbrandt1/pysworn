from pysworn.datasworn import index
from rich import print
from rich.panel import Panel


def main():
    from pysworn.renderables import RENDERABLES

    for link, v in index.items():
        # if "delve_site:" not in link:
        # continue
        rule_type = link
        if ":" in link:
            rule_type = link.split(":")[0]
        renderable = RENDERABLES.get(rule_type)
        # print(f"[i dim]{link}[/] --> {renderable} {type(index[link]).__name__}")
        if renderable:
            # print(Panel(renderable(index[link])))
            print(renderable(index[link]))


if __name__ == "__main__":
    main()
