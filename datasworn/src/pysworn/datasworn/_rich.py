from rich.pretty import Pretty

from .main import get_parent_id, index


class RichPrintOracleRollableRowText:
    def __init__(self, rule_id, *args, **kwargs):
        self.rule_id = rule_id

    def __rich__(self):
        obj = index[self.rule_id]
        parent = index[get_parent_id(self.rule_id)]
        # {obj.roll.min}-{obj.roll.max}
        return f"{parent.name.value}: {obj.text.value}."
