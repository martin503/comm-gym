from loguru import logger
from tqdm import tqdm


def setup_logging(level: str = 'INFO') -> None:
    """Route loguru output through tqdm.write so progress bars stay intact."""
    logger.remove()
    logger.add(lambda message: tqdm.write(message.rstrip('\n')), level=level, colorize=False)


__all__ = ['logger', 'setup_logging']
