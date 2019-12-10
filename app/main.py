#!/usr/bin/env python3
import csv
from io import StringIO, BytesIO
from datetime import datetime
from decimal import Decimal
from flask import Flask, request, render_template, url_for, Response, send_file
from app import util

app = Flask(__name__)


@app.route("/")
def index():
    members, project = util.get_members()
    return render_template("index.html", members=members)


@app.route("/invoice/<int:idx>")
def invoice(idx):
    start_date = request.values.get("start")
    end_date = request.values.get("end")

    if start_date is not None:
        start_date = datetime.fromisoformat(start_date)
    if end_date is not None:
        end_date = datetime.fromisoformat(end_date)

    ctx = util.parse_invoice_data(start_date=start_date, end_date=end_date, html=True,)

    balance = Decimal(ctx["project"]["balance"][str(idx)]).quantize(util.TWOPLACES)

    return render_template(
        "invoice.html",
        id=idx,
        balance=balance,
        members=ctx["members"],
        project=ctx["project"],
        debts=ctx["debts"].get(idx),
        credits=ctx["credits"].get(idx),
    )


@app.route("/csv/<int:idx>")
def download_csv(idx):
    start_date = request.values.get("start")
    end_date = request.values.get("end")

    if start_date is not None:
        start_date = datetime.fromisoformat(start_date)
    if end_date is not None:
        end_date = datetime.fromisoformat(end_date)

    ctx = util.parse_invoice_data(start_date=start_date, end_date=end_date,)

    fieldnames = ["date", "category", "what", "who", "amount"]
    with StringIO() as csv_buffer:
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()

        if idx in ctx["debts"]:
            for row in ctx["debts"][idx]:
                writer.writerow(row)

        if idx in ctx["credits"]:
            for row in ctx["credits"][idx]:
                writer.writerow(row)

        csv_buffer.seek(0)
        mem = BytesIO()
        mem.write(csv_buffer.getvalue().encode('utf-8'))
        mem.seek(0)
        csv_buffer.close()

        date_string = datetime.today().isoformat()[:10]
        filename = "cospend_invoice-{0}.csv".format(date_string)
    return send_file(
        mem,
        as_attachment=True,
        attachment_filename=filename,
        mimetype="text/csv",
    )


@app.route("/test")
def test_project():
    with open("app/tests/project.json") as f:
        text = f.read()
    return text


@app.route("/test/bills")
def test_bills():
    with open("app/tests/bills.json") as f:
        text = f.read()
    return text
