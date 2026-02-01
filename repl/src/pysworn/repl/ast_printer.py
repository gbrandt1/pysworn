from functools import singledispatchmethod

from pysworn.repl.expr import Binary, Expr, Grouping, Literal, Unary


class AstPrinter:
    """The sworn AST prettyprinter"""

    def _parenthesize(self, name: str, *expressions: Expr) -> str:
        components = [name]
        for expr in expressions:
            components.append(self.visit(expr))  # type: ignore[no-any-return]

        out_str = f"({' '.join(components)})"
        return out_str

    def dump(self, expr: Expr) -> str:
        """Return a formatted dump of the tree in `expr`."""
        return self.visit(expr)  # type: ignore[no-any-return]


class PrefixAstPrinter(AstPrinter):
    """The sworn AST prefix notation printer"""

    @singledispatchmethod
    def visit(self, expr: Expr) -> str:
        raise NotImplementedError(f"visit not implemented for {type(expr)}")

    @visit.register
    def _(self, expr: Binary) -> str:
        return self._parenthesize(expr.operator, expr.left, expr.right)

    @visit.register
    def _(self, expr: Grouping) -> str:
        return self._parenthesize("group", expr.expression)

    @visit.register
    def _(self, expr: Literal) -> str:
        return str(expr.value)

    @visit.register
    def _(self, expr: Unary) -> str:
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

    printer = PrefixAstPrinter()
    print(printer.dump(expression))
