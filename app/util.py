import re
from decimal import Decimal
from typing import Any, List, Dict
import datetime
import requests

from app.config import *

TWOPLACES = Decimal(10) ** -2

PAYMENT_MODES = {
    "c": "Credit Card",
    "b": "Cash",
    "f": "Check",
}

CATEGORIES = {
    -1: {"name": "Groceries"},
    -2: {"name": "Leisure"},
    -3: {"name": "Rent"},
    -4: {"name": "Bills"},
    -5: {"name": "Culture"},
    -6: {"name": "Health"},
    -7: {"name": "Tools"},
    -8: {"name": "Multimedia"},
    -9: {"name": "Clothes"},
    -11: {"name": "Reimbursement"},
}

URL_REGEX = re.compile(r"(https?://[^ ]+)")


class CospendAPI(object):
    def __init__(self, api_url=API_URL):
        self.api_url = api_url
        self.members = None
        self.categories = CATEGORIES
        self.get_members()

    def get_members(self):
        api_response = requests.get(self.api_url).json()
        parsed_members = {}
        for member in api_response["members"]:
            parsed_members[member["id"]] = member

        self.members = parsed_members
        self.categories.update(api_response.get("categories"))

        return self.members, api_response

    def get_active_members(self):
        return [self.members[idx] for idx in self.members if self.members[idx]["activated"]]

    def parse_invoice_data(
        self,
        start_date: datetime.datetime = None,
        end_date: datetime.datetime = None,
        html: bool = False,
    ) -> Dict[str, Any]:
        all_owers = set()

        _, project = self.get_members()

        debts = {}
        credits = {}

        api_response = requests.get("{}/bills".format(self.api_url)).json()

        for row in api_response:
            owers = row["owers"]
            amount_each = Decimal(row["amount"]).quantize(TWOPLACES)
            amount_each /= len(owers)

            row["payer"] = self.members[row["payer_id"]]
            row["payer_name"] = row["payer"]["name"]

            if row["what"] == "deleteMeIfYouWant":
                continue

            if len(owers) > 1:
                what = "1/{0} {1}".format(len(owers), row["what"])
            else:
                what = row["what"]

            if html:
                what = format_urls(what)

            print(what, row["categoryid"])
            category = self.categories.get(row.get("categoryid"))
            #if category["name"] == "" and "rent" in what.lower():
            #    category = "Rent"

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
            "members": self.members,
            "project": project,
        }


def format_urls(inp: str) -> str:
    def sub_url(match: re.Match) -> str:
        return '<a href="{0}">{0}</a>'.format(match.group(1))

    return URL_REGEX.sub(sub_url, inp)
