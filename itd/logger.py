import logging
from sys import stdout


class ShortNameFormatter(logging.Formatter):
    def __init__(
        self, fmt: str | None = None, datefmt: str | None = None, colorful: bool = True
    ) -> None:
        super().__init__(fmt, datefmt)
        self.colorful = colorful

    def format(self, record):
        if record.name == "itd":
            record.display_name = ""
        elif self.colorful:
            record.display_name = f"[bold]{record.name.split('.')[-1]}:[/bold] "
        else:
            record.display_name = f"{record.name.split('.')[-1]}: "
        return super().format(record)


def setup_logging(level: str = "INFO", colorful: bool | None = None) -> logging.Logger:
    level = level.upper()

    base_logger = logging.getLogger("itd")
    base_logger.propagate = False

    for h in list(base_logger.handlers):
        base_logger.removeHandler(h)

    RichHandler = None
    if colorful is not False:
        try:
            from rich.logging import RichHandler
        except ImportError:
            pass

    if RichHandler is not None:
        handler = RichHandler(rich_tracebacks=True, markup=True)
        formatter = ShortNameFormatter("%(display_name)s%(message)s", "%Y-%m-%d %H:%M:%S")
    else:
        handler = logging.StreamHandler(stream=stdout)
        formatter = ShortNameFormatter("%(asctime)s [%(levelname)s] %(display_name)s%(message)s", "%Y-%m-%d %H:%M:%S", False)

    handler.setFormatter(formatter)

    base_logger.setLevel(level)
    base_logger.addHandler(handler)

    return base_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f'itd.{name}')
