class Catalogue:
    verbose: bool = False  # expect: R57

    def __init__(self, strict: bool) -> None:  # expect: R57
        self.enabled = True  # expect: R57
        self.is_loaded = False

    def search(self, term: str, exact: bool = False) -> list[str]:  # expect: R57
        return [term]


def renew(loan_id: str, *, force: bool = False) -> None:  # expect: R57
    pass


def export(rows: list[str], include_header: bool = True) -> str:  # expect: R57
    return "\n".join(rows)


def archive(*, do_it: bool = False) -> None:  # expect-llm: R57
    pass


catalogue = Catalogue(strict=True)
catalogue.search("dune", True)  # expect: R57
renew_all(["loan-1"], False, True)  # expect: R57
