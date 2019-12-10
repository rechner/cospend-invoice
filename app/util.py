import re
from decimal import Decimal
from typing import Any, List, Dict
import datetime
import requests
from jinja2 import Markup

from app.config import *

TWOPLACES = Decimal(10) ** -2
CATEGORIES = {
    -1: "Groceries",
    -2: "Leisure",
    -3: "Rent",
    -4: "Bills",
    -5: "Culture",
    -6: "Health",
    -7: "Tools",
    -8: "Multimedia",
    -9: "Clothes",
}

PAYMENT_MODES = {
    "c": "Credit Card",
    "b": "Cash",
    "f": "Check",
}

URL_REGEX = re.compile(r"(https?://[^ ]+)")


def get_members(api_url=API_URL):
    api_response = requests.get(api_url).json()
    parsed_members = {}
    for member in api_response["members"]:
        parsed_members[member["id"]] = member

    return parsed_members, api_response


def get_active_members(members):
    return [members[idx] for idx in members if members[idx]["activated"]]


# if len(sys.argv) != 2:
#    print("Usage: {0} file.csv".format(sys.argv[0]))
#    exit(1)


def parse_invoice_data(
    start_date: datetime.datetime = None,
    end_date: datetime.datetime = None,
    html: bool = False,
) -> List[Dict[str, Any]]:
    all_owers = set()

    members, project = get_members(API_URL)

    debts = {}
    credits = {}

    api_response = requests.get("{}/bills".format(API_URL)).json()

    for row in api_response:
        owers = row["owers"]
        amount_each = Decimal(row["amount"]).quantize(TWOPLACES)
        amount_each /= len(owers)

        row["payer"] = members[row["payer_id"]]
        row["payer_name"] = row["payer"]["name"]

        if row["what"] == "deleteMeIfYouWant":
            continue

        if len(owers) > 1:
            what = "1/{0} {1}".format(len(owers), row["what"])
        else:
            what = row["what"]

        if html:
            what = format_urls(what)

        category = CATEGORIES.get(row.get("category_id"), "")
        if category == "" and "rent" in what.lower():
            category = "Rent"

        doc = {
            "date": row["date"],
            "who": row["payer_name"],
            "amount": amount_each.quantize(TWOPLACES),
            "what": what,
            "category": category,
        }

        date = datetime.datetime.fromisoformat(row["date"])
        if start_date is not None and date < start_date:
            continue

        if end_date is not None and date > end_date:
            continue

        for ower in owers:
            all_owers.add(ower["name"])
            if ower["id"] not in debts:
                debts[ower["id"]] = [
                    doc,
                ]
            else:
                debts[ower["id"]].append(doc)

        doc = {
            "date": row["date"],
            "who": row["payer_name"],
            "amount": -amount_each.quantize(TWOPLACES),
            "what": what,
            "category": category,
        }

        if row["payer_id"] not in credits:
            credits[row["payer_id"]] = [
                doc,
            ]
        else:
            credits[row["payer_id"]].append(doc)

    return {
        "debts": debts,
        "credits": credits,
        "members": members,
        "project": project,
    }


def format_urls(inp: str) -> str:
    def sub_url(match: re.Match) -> str:
        url = match.group(1)
        return '<a href="{0}">{0}</a>'.format(match.group(1))

    return URL_REGEX.sub(sub_url, inp)
