def describe(reading) -> str:
    if isinstance(reading, Rain):  # expect: R67
        return f"{reading.mm} mm rain"
    elif isinstance(reading, Snow):
        return f"{reading.cm} cm snow"
    else:
        return "dry"


def retry_delay(err: Exception) -> float:
    if isinstance(err, Timeout):  # expect: R67
        return 1.0
    if isinstance(err, Refused):
        return 5.0
    raise err


def shelf_for(item) -> str:
    if item.archived:
        return "basement"
    elif isinstance(item, (Book, Magazine)):  # expect: R67
        return "reading room"
    elif item.size > 3:
        return "oversize"
    elif isinstance(item, Map):
        return "map drawer"
    return "general"


def postage(parcel) -> int:
    match parcel:  # expect: R67
        case Letter():
            return 1
        case Box(weight=w):
            return 3 + w
