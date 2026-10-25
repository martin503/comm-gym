from pathlib import Path

from loguru import logger


def comma_list(value: str) -> list[str]:
    """argparse type for comma-separated, whitespace-padded, non-empty items."""
    return [item.strip() for item in value.split(',') if item.strip()]


def write_report(path: Path, lines: list[str]) -> None:
    """Write a markdown report, creating parent directories, and log the destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')
    logger.info('report written to {}', path)
