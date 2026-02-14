from pysworn.common import datasworn_tree
from pysworn.renderables import get_renderable
from rich.console import RenderableType
from rich.markdown import Markdown


def pages(render: bool = False) -> list[RenderableType]:
    page_index = {}
    for k, v in datasworn_tree.index.items():
        title = None
        page = None
        if source := getattr(v, "source", None):
            # print(source)
            title = source.title
            page = source.page or -1

        if title is None or page is None:
            continue

        d = page_index.setdefault(title, {})
        dd = d.setdefault(page, {})
        dd[k] = v

    renderables = []
    for title in sorted(page_index.keys()):
        renderables.append(Markdown(f"# {title}"))
        # tree = Tree(f"{title}")
        for page in sorted(page_index[title].keys()):
            # print(Rule(f"{page:4}", align="left"))
            # node = tree.add(f"{page:4}")
            for k, v in page_index[title][page].items():
                renderables.append(
                    f"{page:4} {f"'{k}'"} <{type(v).__name__}>"
                    # f"{renderable}",
                )
                # print(Pretty(v))
                if render:
                    renderable = get_renderable(v)
                    renderables.append(renderable)
                # node.add(k)

    return renderables
