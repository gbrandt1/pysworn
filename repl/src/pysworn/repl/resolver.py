
class Resolver:
    """The Sworn resolver"""
    def __init__(self, interpreter) -> None:
        self._interpreter = interpreter
        self._scopes: list[dict[str, bool]] = []
        
        # self._current_func =
    
        def _begin_scope(self) -> None:
        self._scopes.append({})

        def _end_scope(self) -> None:
            self._scopes.pop()

        def _resolve_one(self, stmt: t.Union[grammar.Stmt, grammar.Expr]) -> None:
            stmt.accept(self)

