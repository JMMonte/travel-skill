"""Lazy primp import — only needed for 'common' fetch mode (which is blocked by Google consent)."""


class Response:
    """Stub response class for type compatibility."""
    status_code: int = 200
    text: str = ""
    text_markdown: str = ""


try:
    from primp import Client  # type: ignore
except ImportError:
    class Client:  # type: ignore[no-redef]
        """Stub client — primp not installed. Only 'local' fetch mode works."""
        def __init__(self, **kwargs):
            pass
        def get(self, url, **kwargs):
            raise RuntimeError("primp not installed. Use fetch_mode='local' instead.")


__all__ = ["Client", "Response"]
