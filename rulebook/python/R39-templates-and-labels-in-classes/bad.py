import string


class Template(str):
    def __call__(self, **values: object) -> str:
        return self.format(**values)


STATION_ONLINE = Template("{station} online since {time}")  # expect: R39
READING_LATE: Template = Template("{station} reading is {minutes} min late")  # expect: R39
DIGEST = string.Template("$count readings today")  # expect: R39


class Messages:  # expect: R39
    STORM_WARNING: Template = Template("storm near {station}")
    REFRESH_HELP = "Refresh every station"  # expect: R39


class Labels:
    UNITS_OPTION = "Units to display"
    GUST_ALERT: Template = Template("gust of {speed} km/h")  # expect: R39


SYNC_HELP = "Sync readings from all stations"  # expect-llm: R39
