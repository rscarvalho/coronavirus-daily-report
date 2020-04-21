from datetime import date
from .base import RegexParser


class MassachusettsParser1(RegexParser):
    patterns = {
        "cases": r"Cases Reported\s*?=\s*([\d,]+)",
        "deaths": r"Deaths.+?Attributed to COVID-19\s+([\d,]+)",
        "test_positive":
        r"Total (?:Patients Tested|Tested\* Patients).*?([\d,]+?)\s",
        "test_total":
         r"Total (?:Patients Tested\*|Tested\* Patients).*?(?:[\d,]+?)\s+([\d,]+)",
    }

    end_date = date(2020, 4, 19)


    def get_url(self, partition):
        month = partition.strftime("%B").lower()
        datepart = partition.strftime("%-d-%Y")
        return f"https://www.mass.gov/doc/covid-19-cases-in-massachusetts-as-of-{month}-{datepart}/download"


    def can_parse(self, state, partition):
        return state == 'ma' and partition <= self.end_date


class MassachusettsParser2(RegexParser):
    start_date = date(2020, 4, 20)

    patterns = {
        "cases": r"Confirmed[ ]?Cases\s*?([\d,]+)",
        "deaths": r"Deaths of[ ]?Confirmed[ ]?COVID-19 Cases\s*?([\d,]+)",
        "test_positive": r"Confirmed[ ]?Cases\s*?([\d,]+)",
        "test_total": r"Total Tests[ ]?Performed\s*?([\d,]+)"
    }

    def get_url(self, partition):
        month = partition.strftime("%B").lower()
        datepart = partition.strftime("%-d-%Y")
        return f"https://www.mass.gov/doc/covid-19-dashboard-{month}-{datepart}/download"

    def can_parse(self, state, partition):
        return state == 'ma' and partition >= self.start_date
