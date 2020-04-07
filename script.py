#!/usr/bin/env python3

import logging
import os
import os.path as path
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
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

handler = FileHandler("script.log")
logging.basicConfig(handlers=[handler], level=logging.DEBUG)

cases_pattern = re.compile(
    r"Cases Reported\s*?=\s*?(?P<cases>\d+)(.*Deaths.+?Attributed to COVID-19\s+(?P<deaths>\d+))?",
    re.MULTILINE | re.IGNORECASE)



def download_files():
    start_date = date(2020, 3, 20)
    end_date = date.today()

    download_url = "https://www.mass.gov/doc/covid-19-cases-in-massachusetts-as-of-{}-{}/download"
    # Let's impersonate a Chrome browser so the website doesn't block us
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"

    for i in range((end_date - start_date).days + 1):
        current = start_date + timedelta(days=i)

        url = download_url.format(
            current.strftime("%B").lower(),
            current.strftime("%-d-%Y")
        )

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
        except Exception as e:
            print("Error downloading file for {} at {}".format(current.strftime("%Y-%m-%d"), url), file=sys.stderr)
            logging.error("Error downloading file {}".format(url), e)


def run_analisys():
    out_writer = csv.writer(sys.stdout)
    out_writer.writerow(["date", "cases", "deaths"])
    for f in sorted(os.listdir("downloads")):
        if not f.endswith(".pdf"):
            continue
        file_path = path.join("downloads", f)
        processing_date = f.replace(".pdf", "")
        with open(file_path, 'rb') as fp:
            logging.info(f"processing file={file_path}")
            stats = process_document(fp, file_path.replace(".pdf", ".txt"))
        if stats:
            out_writer.writerow([processing_date, stats['cases'], stats['deaths']])
        else:
            logging.warn(f"could not find info for file={file_path}")


def process_document(fp, out_file):
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
    match = cases_pattern.search(contents)
    if match:
        return {k: int(v) for k, v in match.groupdict().items()}
    return None


if __name__ == "__main__":
    download_files()
    run_analisys()
