class NotFound(Exception):
    """The requested record does not exist. The API maps this to 404."""


class Conflict(Exception):
    """The request is valid but the record's current state does not allow it. Maps to 409."""


class InvalidInput(Exception):
    """The request body parsed but its content is unusable (for example a malformed CSV). 422."""


class UpstreamError(Exception):
    """An external provider (such as the copy model) failed. Maps to 502."""
