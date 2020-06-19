#!/usr/bin/env python3

import logging
import os
import os.path as path
import re
import shutil
import sys
import urllib.error
import urllib.request
from urllib.error import HTTPError
from datetime import date, datetime, timedelta
from io import StringIO
from logging import StreamHandler, FileHandler
import csv

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTChar, LTTextBox, LTTextLine
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfdocument import PDFDocument, PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from parser.massachusetts import MassachusettsParser1, MassachusettsParser2, MassachusettsParser3, MassachusettsParser4
from parser.base import ParsedRecord

handler = FileHandler("script.log")
logging.basicConfig(handlers=[handler], level=logging.DEBUG)


ALL_PARSERS = (MassachusettsParser1(), MassachusettsParser2(), MassachusettsParser3(), MassachusettsParser4())

def download_files():
    state = 'ma'
    start_date = date(2020, 3, 20)
    end_date = date.today()

    download_url = "https://www.mass.gov/doc/covid-19-cases-in-massachusetts-as-of-{}-{}/download"
    # Let's impersonate a Chrome browser so the website doesn't block us
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"

    for i in range((end_date - start_date).days + 1):
        current = start_date + timedelta(days=i)
        parsers = [p for p in ALL_PARSERS if p.can_parse(state, current)]

        if not parsers:
            logging.error(f"Cannot find a parser for state={state}, date={current}")
            continue
        parser = parsers[0]

        url = parser.get_url(current)

        output = path.join("downloads", f"{current.strftime('%Y-%m-%d')}.pdf")

        if path.exists(output):
            logging.info(f"File {output} already exists")
            continue

        logging.debug(url)

        headers = {
            "User-agent": user_agent
        }
        req = urllib.request.Request(url=url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response, open(output, 'wb') as w:
                shutil.copyfileobj(response, w)
                logging.info(f"Downloaded file {output}")
        except HTTPError as e:
            print("[NOT FOUND] Could not download file for {} at {}".format(current.strftime("%Y-%m-%d"), url),
                    file=sys.stderr)
        except Exception as e:
            print("Error downloading file for {} at {}".format(current.strftime("%Y-%m-%d"), url), file=sys.stderr)
            logging.error("Error downloading file {}".format(url), e)


def run_analisys():
    state = 'ma'
    out_writer = csv.writer(sys.stdout, lineterminator=os.linesep)
    out_writer.writerow(["date"] + ParsedRecord.header())

    with open('stats.csv') as in_file:
        processed_dates = {datetime.strptime(r["date"], "%Y-%m-%d").date(): r for r in csv.DictReader(in_file)}

    for f in sorted(os.listdir("downloads")):
        if not f.endswith(".pdf"):
            continue
        file_path = path.join("downloads", f)
        processing_date_str = f.replace(".pdf", "")
        processing_date = datetime.strptime(processing_date_str, "%Y-%m-%d").date()

        if processing_date in processed_dates:
            logging.info(f"Already processed for date={processing_date.isoformat()}")
            r = processed_dates[processing_date]
            record = ParsedRecord(r["cases"], r["deaths"], r["test_total"], r["test_positive"])
            out_writer.writerow([r["date"]] + record.row)
            continue

        with open(file_path, 'rb') as fp:
            logging.info(f"processing file={file_path}")
            stats = process_document(state, processing_date, fp, file_path.replace(".pdf", ".txt"))
            logging.info(f"Stats for date={processing_date_str} - {stats}")
        if stats:
            out_writer.writerow([processing_date_str] + stats.row)
        else:
            logging.warning(f"could not find info for file={file_path}")


def process_document(state, processing_date, fp, out_file):
    if path.exists(out_file):
        contents = open(out_file, "rb").read().decode("utf-8")
    else:
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        if not doc.is_extractable:
            raise PDFTextExtractionNotAllowed
        mgr = PDFResourceManager()
        device = PDFPageAggregator(mgr)
        interpreter = PDFPageInterpreter(mgr, device)

        contents = ""
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
            layout = device.get_result()
            for element in layout:
                if isinstance(element, LTChar):
                    contents += element.get_text()
        open(out_file, "wb").write(contents.encode("utf-8"))

    parsers = [p for p in ALL_PARSERS if p.can_parse(state, processing_date)]
    if not parsers:
        return None

    parser = parsers[0]
    return parser.parse_document(contents)



if __name__ == "__main__":
    download_files()
    run_analisys()
