from pathlib import Path

LABEL_SUFFIX = ".pdf"


class Parcel:
    def __init__(self, code, weight_g, events):
        self.code = code
        self.weight_g = weight_g
        self.events = events

    def weight_kg(self):  # expect: R6
        return self.weight_g / 1000

    def lines(self):  # expect: R6
        return [f"{e.when:%H:%M} {e.place}" for e in sorted(self.events)]

    def label_path(self):  # expect: R6
        return Path(self.spool_dir).joinpath(self.code).with_suffix(LABEL_SUFFIX)

    def tracking_code(self):  # expect: R6
        return self.code.strip().upper()

    @property
    def history(self):
        return Path(f"{self.code}.log").read_text()  # expect: R6

    @property
    def status(self):
        print(self.events[-1].place)  # expect: R6
        return self.events[-1].place


class Depot:
    def parcels_by_code(self):
        return {}


def busy_codes(depot):
    return sorted(depot.parcels_by_code().keys())  # expect-llm: R6
