import logging
import random
from typing import Tuple

from pysworn.datasworn import index
from pysworn.datasworn._datasworn import OracleRollableTableTableText

from ._rich import markup, plain


def get_rows(otr: OracleRollableTableTableText):
    if not hasattr(otr, "rows"):
        return []
        # msg = f"OracleRollableTableText {otr} has no rows"
        # raise ValueError(msg)
    rows = []
    for row in otr.rows:
        roll = getattr(row, "roll", None)
        if roll is None:
            logging.warning(f"Row {row} has no roll")
            continue
        min_ = roll.min
        max_ = roll.max
        if min_ is None or max_ is None:
            continue
        if min_ < max_:
            roll = f"{min_}-{max_}"
        else:
            roll = f"{min_}"
        rows.append(
            [
                roll,
                markup(getattr(row, "text", None)),
                markup(getattr(row, "text2", None)),
                markup(getattr(row, "text3", None)),
            ]
        )
        # logging.debug(rows[-1])
    # logging.debug(f"Found {len(rows)}")
    return rows


def get_max_row_widths(otr: OracleRollableTableTableText) -> tuple[int, int, int]:
    if not hasattr(otr, "rows"):
        msg = f"OracleRollableTableText {otr} has no rows"
        raise ValueError(msg)
    text = 0
    text2 = 0
    text3 = 0
    for row in otr.rows:
        text = max(text, len(plain(row.text)))
        if not hasattr(row, "text2"):
            continue
        text2 = max(text2, len(plain(row.text2)))
        if not hasattr(row, "text3"):
            continue
        text3 = max(text3, len(plain(row.text3)))
    return (text, text2, text3)


def get_dimensions(otr: OracleRollableTableTableText) -> tuple[int, int]:
    rows = get_rows(otr)
    maxwidth = 0
    maxheight = 0
    for row in rows:
        maxwidth = max(maxwidth, len(" ".join(row)))
        maxheight = max(maxheight, len(rows))
    return (maxwidth, maxheight)


def get_row(otr: OracleRollableTableTableText, n: int):
    # dice = otr.dice.value
    # print(dice)
    for row in otr.rows:
        min_ = getattr(row, "min")
        max_ = getattr(row, "max")
        if min_ is None or max_ is None:
            return None
        if min_ <= n <= max_:
            text = markup(getattr(row, "text", None))
            text2 = markup(getattr(row, "text2", None))
            text3 = markup(getattr(row, "text3", None))
            return [text, text2, text3]
    return None


def get_row_by_index(otr: OracleRollableTableTableText, n: int) -> list[str]:
    row = otr.rows[n]
    roll = row.roll
    if roll:
        dice_range = f"{roll.min}-{roll.max}"
    else:
        dice_range = "-"
    text = markup(getattr(row, "text", None))
    text2 = markup(getattr(row, "text2", None))
    text3 = markup(getattr(row, "text3", None))
    return [dice_range, text, text2, text3]


def get_row_from_link(link: str) -> Tuple[str, str]:
    """
    Get a row from a link like 'oracle_id;row_index'
    """
    if ";" in link:
        oracle_id, row_index = link.split(";")
        otr = index[oracle_id]
        n = int(row_index.split("-")[0])
        row = get_row(otr, n)
    else:
        # no roll specified, roll now
        oracle_id = link
        otr = index[oracle_id]
        n = {
            "1d6": random.randint(1, 6),
            "1d10": random.randint(1, 10),
            "1d20": random.randint(1, 20),
            "1d100": random.randint(1, 100),
            "1d200": random.randint(1, 200),
            "1d300": random.randint(1, 300),
        }[otr.dice.value]
        row = get_row(otr, n)

    if oracle_id not in index:
        logging.error(f"Oracle {oracle_id} not found in index")
        return "not found", oracle_id
    name = f"{otr.name.value}" if hasattr(otr, "name") else ""
    if not row:
        logging.error(f"Row {n} not found in oracle {oracle_id}")
        return ""
    result = row[0] + "."
    if row[1]:
        result += " " + row[1] + "."
    if row[2]:
        result += " " + row[2] + "."
    return name, result


def get_name_or_canonical(obj):
    if hasattr(obj, "canonical_name") and obj.canonical_name:
        return obj.canonical_name.value
    else:
        return obj.name.value


def get_row_number(otr: OracleRollableTableTableText, n: int) -> int | None:
    nrow = 0
    for row in otr.rows:
        roll = row.roll
        if roll is None:
            nrow += 1
            continue
        min_ = roll.min
        max_ = roll.max
        if min_ is None or max_ is None:
            return None
        if min_ <= n <= max_:
            return nrow
        nrow += 1
    return None
