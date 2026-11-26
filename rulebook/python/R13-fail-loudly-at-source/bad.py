class HandOverError(Exception):
    pass


def _raise_if_refused(receipt):
    """Raise when the courier refused the parcel."""
    if receipt.refused:
        raise HandOverError(receipt.reason)


def deliver(courier, parcel):
    receipt = courier.hand_over(parcel)
    _raise_if_refused(receipt)  # expect: R13
    return receipt


def redeliver(courier, parcel):
    parcel.attempts += 1
    receipt = courier.hand_over(parcel)
    _raise_if_refused(receipt)  # expect: R13


class Scanner:
    def _ensure_scanned(self, status):
        if status.code != 0:
            raise HandOverError(status.text)

    async def check_in(self, code):
        status = await self.scan(code)
        self._ensure_scanned(status)  # expect: R13
        return status

    def weigh(self, parcel):
        grams = self.scale.read(parcel)  # expect-llm: R13
        if grams is None:
            raise HandOverError("scale failed")
        return grams
