import click


class Catalogue:
    DEBUG: bool = False  # an upper-case setting, not a bare-word flag
    is_verbose: bool = False

    def __init__(self, *, is_strict: bool) -> None:
        self.search_enabled = True
        self.is_loaded = False

    @property
    def is_open(self) -> bool:
        return self._is_open

    @is_open.setter
    def is_open(self, value: bool) -> None:  # the setter's signature is fixed by the property protocol
        self._is_open = value

    def search(self, term: str, *, is_exact: bool = False) -> list[str]:
        found: bool = False  # a local, not an attribute
        return [term] if found or is_exact else []


def renew(loan_id: str, *, force_overdue: bool = False) -> None:
    pass


@click.command()
@click.option("--off", "is_off", is_flag=True)  # the CLI flag keeps its name
def main(*, is_off: bool) -> None:
    catalogue: Catalogue = Catalogue(is_strict=True)
    catalogue.search("dune", is_exact=True)
    options: dict[str, bool] = {}
    options.get("exact", False)
    getattr(catalogue, "is_loaded", False)
    options.setdefault("strict", True)
