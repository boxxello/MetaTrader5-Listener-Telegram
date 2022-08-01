import asyncio
import logging
import multiprocessing
import os
import sys
import threading
from datetime import time, datetime

from os.path import isfile, join
import time
from threading import Thread
from telethon import TelegramClient, events
from bot import Bot
from ocr import Ocr
from const import data_constants, const_dirs

from runfile import Executable
from telegram_h import Telegram_c

from utils import check_pattern, get_random_img_str_from_dir, is_first_day_of_month
from apscheduler.schedulers.background import BackgroundScheduler
import keyboard


class Listener:
    def __init__(self, logger: logging.Logger, session_name: str = None):
        self.const = data_constants(logger)
        self.logger = logger
        self.ocr = Ocr(logger, const_dirs.TESSERACT_PATH)
        self.bots = [Bot(logger, True, True, False, **data) for data in self.const.mt_data]
        self.scheduler = BackgroundScheduler({'apscheduler.timezone': 'Europe/Berlin'})
        self.scheduler_var = True
        cpu_count_t = os.cpu_count()
        if cpu_count_t > 1:
            cpu_count_t -= 1
        self.pool = multiprocessing.Pool(processes=cpu_count_t)

        self.telegram = Telegram_c(self.const.CHANNEL_NAME, self.const.TELEGRAM_API_ID,
                                   self.const.TELEGRAM_API_HASH,
                                   self.const.SESSION_NAME)
        self.define_handler(channel_id=self.telegram.channel_id)

    def define_handler(self, channel_id):
        # uncomment to test in telegram channel by sending it by yourself
        # @self.telegram.client.on(events.NewMessage(outgoing=True, chats=channel_id))
        @self.telegram.client.on(events.NewMessage(incoming=True, chats=channel_id))
        async def handler(event):
            if event.photo:
                self.telegram.logger.info("Message containing image detected!")
                filename = datetime.now().strftime("%d-%m-%y_%H%M%S%f")[:-3]
                filename += ".jpg"
                path = os.path.join(const_dirs.TEMP_DIR, filename)

                await event.message.download_media(file=path)
                self.telegram.logger.info(f"Running script on {filename}")
                data = self.get_processed_data(path)
                if data:
                    for bot in (bot for bot in self.bots if bot.status.value == True):
                        bot.connect(bot.trader.trade, data)

    def get_processed_data(self, path):
        data = self.ocr.extract_data(path)

        processed_data = check_pattern(data)
        # if not processed_data:
        #     self.ocr.show_img_on_window_by_path(path)
        return processed_data

    def add_new_bot(self, logger: logging.Logger, status: bool, freq_check: bool, reactivate_next_month: bool,
                    data_dict: dict):
        self.bots.append(Bot(logger, status, freq_check, reactivate_next_month, **data_dict))

    def get_rand_img_and_test(self):
        file_path = join(const_dirs.TEMP_DIR, get_random_img_str_from_dir(const_dirs.TEMP_DIR))
        self.logger.info("Extracting from  %s" % str(file_path))
        processed_data = self.get_processed_data(file_path)
        return processed_data, file_path

    def deactivate_bot(self, lst_tuple: list):
        for x, k, s, u in lst_tuple:
            for bot in self.bots:
                if k == bot.login:
                    self.logger.info(f"Deactivating bot with credentials: {bot.login}")
                    bot.status.value = False
                    self.logger.info(f"Modifying devs for acc {bot.login} ")
                    self.const.modify_vol_from_percentage(k, s)
                    bot.trader.reload_devs()

    def activate_bots(self):
        for bot in self.bots:
            bot.status.value = True

    def scheduler_activate(self):

        """
        if it's the first day of the month then it should run by itself.
        if it's not then we are going to manually start the background fn.
        if it's the last day of the month and the fn is still running then we
        are going to shut it down by setting a global var to false (which is also checked
        fn while loop).
        """
        self.logger.info("Starting the background scheduler")
        job = self.scheduler.add_job(self.run_function_bg, trigger='cron', year='*', month='*',
                                     day='1',
                                     max_instances=1, id='1_month')
        job_deactivate = self.scheduler.add_job(self.set_scheduler_var_to_false, trigger='cron',
                                                day='last', hour="23", minute="59", second="58",
                                                max_instances=1, id='job_deactivate')
        self.scheduler.add_job(self.reactivate_bots_next_month, trigger='cron',
                               day='last', hour="23", minute="59", second="59",
                               max_instances=1, id='job_reactivate_next_month')
        self.logger.info("Manually starting the function")
        job.modify(next_run_time=datetime.now())
        # self.logger.info(self.scheduler.get_jobs())
        self.scheduler.start()

    def reactivate_bots_next_month(self):
        for bot in self.bots:
            if bot.reactivate_next_month.value:
                bot.status.value = True

    def set_scheduler_var_to_false(self):
        self.logger.info("stopping the scheduler")
        self.logger.info(self.scheduler.get_jobs())

        # self.scheduler.remove_job(job_id='1_month')
        self.scheduler_var = False
        self.logger.info(
            "Successfully stopped frequency check, you shouldn't be able to see frequency checks anymore")

    def activate_bots_run_scheduler(self):
        self.activate_bots()
        self.scheduler_activate()

    def run_function_bg(self):

        self.scheduler_var = True

        minute = None
        counter = 0
        self.logger.info(f"Starting the multi processing pool with pool: {self.pool}")

        while self.scheduler_var:
            my_lst = [bot for bot in self.bots if bot.status.value == True and bot.freq_check.value == True]
            if my_lst:
                try:
                    # results=[bot.connect(bot.trader.frequency_check_trade,) for bot in my_lst]
                    results = [self.pool.apply(bot.connect, args=(bot.trader.frequency_check_trade,)) for bot in my_lst]

                except KeyboardInterrupt:
                    self.scheduler_var = False
                    self.pool.terminate()
                    self.pool.join()

                # self.logger.info(f"Status active account/Account info/Actual percentage profit/\n{results}")
                if datetime.now().minute != minute:
                    minute = datetime.now().minute
                    counter += 1
                    if counter == int(self.const.MINUTES_FREQUENCY_CHECK_LOG):
                        # for status, info, percent in results: self.logger.info(f"Status {status}/Account info{info}/Actual percentage profit:{percent}")
                        self.logger.info(
                            f"Status active account/Account info/Actual percentage profit/Percentage to meet/\n{results}")
                        counter = 0

                lst_deact = [(freq_check, info, percentage, new_percentage) for
                             freq_check, info, percentage, new_percentage in
                             results if freq_check == False]
                if lst_deact:
                    self.deactivate_bot(lst_deact)
            else:
                self.scheduler_var = False

    def kill_terminal_procs(self):
        lst = [bot.exe_path
               for bot in self.bots]
        success_lst, unable_lst, found_proc = Executable.check_running_program(list_executables_to_check=lst)
        self.logger.info("Trying to kill hanging terminal processes")
        if len(found_proc) > 0:
            if len(success_lst) > 0:
                self.logger.info(f"Successfully shut down {success_lst}")

            if len(unable_lst) > 0:
                self.logger.error(f"Unable to kill these processes: {unable_lst}")
        else:
            self.logger.info("No terminal process was found")

    def are_all_terminals_running_list(self):
        lst = [bot.exe_path
               for bot in self.bots]
        return Executable.check_are_all_terminals_running(list_executables_to_check=lst)

    def run(self):

        self.kill_terminal_procs()

        temp_flag_for_loop = False
        self.logger.info("Waiting for the executables to start")
        while not temp_flag_for_loop:
            for bot in self.bots:
                bot.connect(bot.trader.is_terminal_up)

            if len(self.are_all_terminals_running_list()) == len(self.bots):
                temp_flag_for_loop = True
        Thread(target=self.scheduler_activate).start()
