from datetime import datetime
import logging
import os
import sys
import time
from pathlib import Path
from typing import Union

from const import const_dirs


class _UTCFormatter(logging.Formatter):
    converter = time.gmtime


_loglevel_map = {
    logging.DEBUG   : 'DEBUG',
    logging.INFO    : 'INFO',
    logging.WARNING : 'WARNING',
    logging.ERROR   : 'ERROR',
    logging.CRITICAL: 'CRITICAL',
}
class LastPartFilter(logging.Filter):
    def filter(self, record):
        record.name_last = record.name.rsplit('.', 1)[-1]
        return True


def get_logger(name_file: Union[Path, str], name: str,
               time_utc: bool = True, level=logging.INFO
               ) -> logging.Logger:
    prefix_path=const_dirs.LOG_DIR
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name_last)s | %(message)s ')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(os.path.join(prefix_path, os.path.join(const_dirs.LOG_DIR,name_file+"_LOGGER"+const_dirs.LOG_FILE_SUFFIX)))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    file_handler.addFilter(LastPartFilter())
    stdout_handler.addFilter(LastPartFilter())
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    return logger

def get_logger_no_sysout(name_file: Union[Path, str], name: str,
               time_utc: bool = True, level=logging.INFO
               ) -> logging.Logger:
    prefix_path=const_dirs.LOG_DIR
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name_last)s | %(message)s ')



    file_handler = logging.FileHandler(os.path.join(prefix_path, os.path.join(const_dirs.LOG_DIR,name_file+"_LOGGER"+const_dirs.LOG_FILE_SUFFIX)))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(LastPartFilter())

    logger.addHandler(file_handler)
    return logger

