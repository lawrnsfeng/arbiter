class Template(str):
    def __call__(self, **values: object) -> str:
        return self.format(**values)


class Messages:
    STATION_ONLINE: Template = Template("{station} online since {time}")
    STORM_WARNING: Template = Template("storm near {station}")


Msg = Messages


class Labels:
    REFRESH_HELP = "Refresh every station"
    UNITS_OPTION = "Units to display"


# look-alike: a template built inside a function is not a module constant
def banner(name: str) -> str:
    heading = Template("== {name} ==")
    return heading(name=name)
