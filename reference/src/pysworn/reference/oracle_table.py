# import logging
import random
from operator import le

from pysworn.datasworn.main import index
from rich.markdown import Markdown
from rich.text import Text
from textual import events, on
from textual.binding import Binding
from textual.message import Message
from textual.widgets import DataTable

from ._rich import markdown, markup
from .oracle import get_max_row_widths, get_row_by_index, get_row_number


class OracleTable(DataTable):
    BINDINGS = [
        Binding("r", "roll", "Roll", show=True),
        Binding("enter", "select", "Select", show=True),
    ]

    class Highlighted(Message):
        def __init__(self, row_id: str):
            self.row_id = row_id
            super().__init__()

    class Selected(Message):
        def __init__(self, row_id: str):
            self.row_id = row_id
            super().__init__()

    def __init__(self, oracle_id: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zebra_stripes = True
        self.cursor_type = "row"
        # self.show_header = False
        if oracle_id:
            self.update(oracle_id)

    def action_roll(self):
        # otr = index[self.oracle_id]
        oracle = self.oracle
        m, d = oracle.dice.value.split("d")
        if m != "1":
            msg = f"Only 1dX dice supported, got {oracle.dice.value}"
            raise ValueError(msg)
        dice = random.randint(1, int(d))
        row_number = get_row_number(oracle, dice)
        if row_number is None:
            return
        row = get_row_by_index(oracle, row_number)
        if row is None:
            return
        self.move_cursor(row=row_number, scroll=True)

    def update(self, oracle_id) -> None:
        if ".row" in oracle_id:
            oracle_type, oracle_id_ = oracle_id.split(":")
            oracle_type = oracle_type.split(".")[0]
            oracle_id_ = oracle_id_.split(".")[0]
            oracle_id = f"{oracle_type}:{oracle_id_}"

        self.rule_id = oracle_id
        self.oracle_id = oracle_id
        self.oracle = index[oracle_id]
        #     self.update_from_oracle()

        # def update_from_oracle(self) -> None:
        self.oracle_id = self.oracle.id
        self.clear(columns=True)
        self.border_title = self.oracle.name.value
        if not hasattr(self.oracle, "rows"):
            msg = f"Oracle {self.oracle.id} has no rows"
            raise ValueError(msg)

        rows = self.oracle.rows

        max1, max2, max3 = get_max_row_widths(self.oracle)
        wmax = 68

        if hasattr(self.oracle, "column_labels"):
            cols = self.oracle.column_labels
            self.add_column(cols.roll.value)
            self.add_column(markdown(cols.text), width=min(max1, wmax))
            if hasattr(cols, "text2"):
                self.add_column(markdown(cols.text2), width=min(max2, wmax))
            if hasattr(cols, "text3"):
                self.add_column(markdown(cols.text3), width=min(max3, wmax))
        else:
            self.add_column("R")
            if max1:
                self.add_column("T", width=min(max1, wmax))
            if max2:
                self.add_column("T2", width=min(max2, wmax))
            if max3:
                self.add_column("T3", width=min(max3, wmax))
            self.show_header = False

        for row in rows:
            roll_min = getattr(getattr(row, "roll"), "min", "")
            roll_max = getattr(getattr(row, "roll"), "max", "")
            roll = f"{roll_min}-{roll_max}" if roll_min != roll_max else roll_min

            row_text = []
            row_text.append(roll)

            row_text.append(markup(row.text))
            if hasattr(row, "text2"):
                row_text.append(markup(row.text2))
            if hasattr(row, "text3"):
                row_text.append(markup(row.text3))

            self.add_row(*row_text, height=None, key=row.id.value)

    def on_show(self) -> None:
        total_height = 0
        for row in self.rows.values():
            total_height += row.height
        self.log(f"Total height: {total_height}")
        self._require_update_dimensions = True
        self.styles.height = total_height + 2
        # = (
        #     self.get_content_height() + 3
        # )  # * len(rows) + 3
        self.refresh()

    def action_select(self):
        row = self.oracle.rows[self.cursor_row]
        self.post_message(OracleTable.Selected(row.id.value))

    # @on(events.Key)
    def on_key(self, event: events.Key) -> None:
        # self.log(f"Key: {event.key}")
        self.scroll_to_widget(self)

        if event.key == "r":
            event.stop()
            self.action_roll()
        elif event.key == "enter":
            event.stop()
            row = self.oracle.rows[self.cursor_row]
            #     self.log(f"Row selected {row.id.value}")
            self.post_message(OracleTable.Selected(row.id.value))
        # else:
        self.move_cursor(scroll=True)

    def on_click(self, event: events.Click) -> None:
        event.stop()
        if event.chain == 2:
            self.action_select()

    @on(DataTable.RowHighlighted)
    def on_row_highlighted(self, event):
        event.stop()
        row = self.oracle.rows[self.cursor_row]
        # self.log(f"Row highlighted {row.id.value}")
        self.post_message(OracleTable.Highlighted(row.id.value))
        self.move_cursor(scroll=True)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event):
        event.stop()
        row = self.oracle.rows[self.cursor_row]
        self.log(f"Row selected {row.id.value}")
        self.post_message(OracleTable.Selected(row.id.value))
        self.move_cursor(scroll=True)
