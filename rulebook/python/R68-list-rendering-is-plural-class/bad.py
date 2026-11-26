def overdue_notice(loans) -> str:
    notice = f"Overdue: {loans[0].title}"
    notice += "".join(f"; also {loan.title}" for loan in loans[1:])  # expect: R68
    return notice


def route_line(stops) -> str:
    return f"{stops[0].name} -> {' -> '.join(s.name for s in stops[1:])}"  # expect: R68


class Recipe:
    def method(self) -> str:
        steps = self.steps
        heading = (
            steps[0].title.capitalize()
            + "; then "
            + "; then ".join([s.title for s in steps[1:]])  # expect: R68
        )
        return heading


def shelf_notes(loans) -> str:
    out = ""
    for loan in loans:  # expect-llm: R68
        out += f"{loan.isbn} due {loan.due}\n"
    return out
