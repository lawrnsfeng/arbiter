# <pkg>/errors.py
class ParcelError(Exception):
    """Root error of the parcel tracker."""


class ConfigMissingError(ParcelError):
    """Cross-cutting: every subsystem reads configuration."""


# <pkg>/courier/errors.py
class CourierError(ParcelError):
    pass


class CourierAuthError(CourierError):
    pass


class CourierTimeoutError(CourierError):
    pass


# look-alike: shares the letters of the prefix but not the word; a cross-cutting error on the root
class CourierlessRouteError(ParcelError):
    pass
