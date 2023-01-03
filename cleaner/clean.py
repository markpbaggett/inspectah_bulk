import argparse


class CleanResults:
    def __init__(self, filename):
        self.filename = filename

    def process(self, filename):
        failures = []
        with open(self.filename, 'r') as results:
            for line in results:
                pid = line.split(' ')[0]
                if pid not in failures:
                    failures.append(pid)
        with open(filename, 'w') as actual_failures:
            for failure in failures:
                actual_failures.write(f"{failure}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cleanup failure results.')
    parser.add_argument("-s", "--sheet", dest="sheet", help="Specify original csv.", required=True)
    parser.add_argument(
        "-o", "--output_sheet", dest="output_sheet", help="Specify output sheet.", required=True
    )
    args = parser.parse_args()
    CleanResults(args.sheet).process(args.output_sheet)
