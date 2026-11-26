class ParcelError(Exception):
    """Root error of the parcel tracker."""


class CourierError(ParcelError):
    """Base of the courier subsystem."""


class CourierAuthError(CourierError):
    pass


class CourierTimeoutError(ParcelError):  # expect: R31
    """Original shape: the subsystem base exists, but this error skips it."""


class ScannerError(ParcelError):
    pass


class ScannerJamError(ScannerError):
    pass


class ScannerOfflineError(ParcelError):  # expect: R31
    pass


class LabelPrinterMissingError(ParcelError):  # expect-llm: R31
    """The label-printer subsystem has no base error yet; this belongs under one."""


class WeightLimitError(Exception):  # expect-llm: R31
    """A project error outside the hierarchy."""
