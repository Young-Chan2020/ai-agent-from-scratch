class ProviderError(Exception):
    """Base error for failures reported by an LLM provider."""


class InvalidRequestError(ProviderError):
    """Raised when a provider cannot accept the request."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot currently serve the request."""
