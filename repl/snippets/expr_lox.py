from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol


class Visitor(Protocol):
    @abstractmethod
    def visit_Binary(self, expr: "Binary") -> Any:
        pass

    @abstractmethod
    def visit_Grouping(self, expr: "Grouping") -> Any:
        pass

    @abstractmethod
    def visit_Literal(self, expr: "Literal") -> Any:
        pass

    @abstractmethod
    def visit_Unary(self, expr: "Unary") -> Any:
        pass


class Token(str):
    pass


@dataclass
class Expr:
    @abstractmethod
    def accept(self, visitor: Visitor) -> Any:
        return NotImplemented


@dataclass
class Binary(Expr):
    left: "Expr"
    operator: Token
    right: "Expr"

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_Binary(self)


@dataclass
class Grouping(Expr):
    expression: "Expr"

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_Grouping(self)


@dataclass
class Literal(Expr):
    value: str | float | int

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_Literal(self)


@dataclass
class Unary(Expr):
    operator: Token
    right: "Expr"

    def accept(self, visitor: Visitor) -> Any:
        return visitor.visit_Unary(self)


# grammar: dict[str, Any] = {}

# grammar_: list[Any] = [
#     ("Binary", [("left", "Expr"), ("operator", Token), ("right", "Expr")]),
#     ("Grouping", [("expression", "Expr")]),
#     ("Literal", [("value", object)]),
#     ("Unary", [("operator", Token), ("right", "Expr")]),
# ]

# grammar = {}
# for class_name, fields in grammar_:
#     c = make_dataclass(class_name, fields, bases=(Expr,))
#     print(f"{c!r}")
#     grammar[class_name] = c


class AstPrinter:
    """The pylox AST prettyprinter!"""

    def _parenthesize(self, name: str, *expressions: Expr) -> str:
        components = [name]
        for expr in expressions:
            components.append(expr.accept(self))

        out_str = f"({' '.join(components)})"
        return out_str

    def dump(self, expr: Expr) -> str:
        """Return a formatted dump of the tree in `expr`."""
        return expr.accept(self)  # type: ignore[no-any-return]

    def visit_Binary(self, expr: Binary) -> str:
        return self._parenthesize(expr.operator, expr.left, expr.right)

    def visit_Grouping(self, expr: Grouping) -> str:
        return self._parenthesize("group", expr.expression)

    def visit_Literal(self, expr: Literal) -> str:
        return str(expr.value)

    def visit_Unary(self, expr: Unary) -> str:
        return self._parenthesize(expr.operator, expr.right)


if __name__ == "__main__":
    # Example usage:
    expression = Binary(
        left=Unary(
            operator="-",
            right=Literal(value=123),
        ),
        operator="*",
        right=Grouping(
            expression=Literal(value=45.67),
        ),
    )

    printer = AstPrinter()
    print(printer.dump(expression))
