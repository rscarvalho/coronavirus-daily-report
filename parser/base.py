import re

class ParsedRecord(object):
    def __init__(self, total_cases: int, total_deaths: int, total_tests: int, total_positive_tests: int):
        self.cases = total_cases
        self.deaths = total_deaths
        self.tests = total_tests
        self.positive_tests = total_positive_tests

    @property
    def row(self):
        return [self.cases, self.deaths, self.tests, self.positive_tests]

    @staticmethod
    def header() -> tuple:
        return ['cases', 'deaths', 'test_positive', 'test_total']

    def __repr__(self):
        return f"ParsedRecord{vars(self)}"



class BaseParser(object):
    def can_parse(self, state, date) -> bool:
        return False

    def get_url(self, date) -> str:
        raise NotImplementedError()

    def parse_document(self, document_text: str) -> ParsedRecord:
        raise NotImplementedError()


class RegexParser(BaseParser):
    patterns = {}

    def parse_document(self, document_text):
        args = []
        for key in ParsedRecord.header():
            if key not in self.patterns:
                return None

            match = re.search(self.patterns[key], document_text, re.I | re.M)
            if not match:
                return None

            args.append(int(match.groups()[0].replace(",", "")))
        return ParsedRecord(*args)
