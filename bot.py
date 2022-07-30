from datetime import datetime
import logging
import os

import pymt5adapter as mt5
from logger import get_logger, get_logger_no_sysout

from const import const_dirs
from object_holding_value import Object_Value_Notify
from trader import Trader


class Bot:
    def __init__(self, logger: logging.Logger, status: bool, freq_check: bool, reactivate_next_month: bool, MT_LOGIN,
                 MT_SERVER: str, MT_PASSWORD: str, devs_path, MT_EXE_PATH=None):
        self.logger = logger
        self.login = MT_LOGIN
        self.server = MT_SERVER
        self.password = MT_PASSWORD
        self.exe_path = MT_EXE_PATH
        self.trader = Trader(devs_path, get_logger(
            name_file="mt5_trader_",
            name=f"Bot_{self.login}", time_utc=True, level=logging.INFO))
        self.status = Object_Value_Notify(status)
        self.status.register_callback(self.log_if_status_changes)

        self.freq_check = Object_Value_Notify(freq_check)
        self.freq_check.register_callback(self.log_if_frequency_changes)

        self.reactivate_next_month = Object_Value_Notify(reactivate_next_month)
        self.reactivate_next_month.register_callback(self.log_if_reactivate_next_month_changes)

        # self.logger = get_logger(path_to_logfile=os.path.join(const_dirs.LOG_DIR,"mt5_trader_"+const_dirs.LOG_FILE_SUFFIX), loglevel=logging.INFO, time_utc=True)

    def log_if_reactivate_next_month_changes(self, old_val, new_val):
        if old_val == new_val:
            self.trader.logger.warning(
                f"Tried to change reactivate next month check to {new_val} but it was already {old_val}")
        else:
            self.trader.logger.info(f"Reactivate next month has changed from {old_val} to {new_val}")

    def log_if_frequency_changes(self, old_val, new_val):
        if old_val == new_val:
            self.trader.logger.warning(f"Tried to change percentage check to {new_val} but it was already {old_val}")
        else:
            self.trader.logger.info(f"Percentage check has changed from {old_val} to {new_val}")

    def log_if_status_changes(self, old_val, new_val):
        if old_val == new_val:
            self.trader.logger.warning(f"Tried to change status to {new_val} but it was already {old_val}")
        else:
            self.trader.logger.info(f"Status has changed from {old_val} to {new_val}")

    def connect(self, function, *args, **kwargs):

            mt5_connected = mt5.connected(
                path=self.exe_path,
                server=self.server,
                login=self.login,
                password=self.password,
                timeout=5000,
                logger=None,  # default is None
                ensure_trade_enabled=True,  # default is False
                enable_real_trading=True,
                raise_on_errors=False,  # default is False
                return_as_dict=False,
                return_as_native_python_objects=False,
            )
            try:
                with mt5_connected:

                    try:
                        return function(*args, **kwargs)
                    except mt5.MT5Error as e:
                        self.logger.critical(f"ERROR RAISED {e} ERRCODE: {e.error_code}")
            except mt5.MT5Error as e:
                if e.error_code == -10001:
                    self.logger.error("Unable to initialize terminal, restart the script")
                    exit(-10)
                else:
                    self.logger.critical(f"ERROR RAISED {e} ERRCODE: {e.error_code}")