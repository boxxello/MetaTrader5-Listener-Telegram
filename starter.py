import asyncio
import logging
import os
import re
import signal
import sys
import threading
import time
from os.path import isfile, join

import aioconsole

from logger import get_logger
from const import const_dirs
from listener import Listener
import pymt5adapter as mt5

from object_holding_value import Object_Value_Notify


async def input_acc_info(listener: Listener, msg1: str, *args, **kwargs) -> tuple:
    choice_2 = None
    listener.logger.info(f"Printing accounts login ")
    for bot in listener.bots:
        listener.logger.info(f"{repr(bot.login)}")
    try:
        choice_2 = await aioconsole.ainput(msg1)
        choice_2 = int(choice_2)
        bot_login_st = [bot.login for bot in listener.bots]
        if not choice_2 in bot_login_st:
            listener.logger.warning(f"No account with login {choice_2} was found in bot list")
    except ValueError as e:
        listener.logger.error("String value was inputted for login info")
        return False, choice_2
    return True, choice_2


def test_account(logger: logging.Logger, status: bool, login_info: int, password: str, server, path):
    mt5_connected = mt5.connected(
        path=path,
        server=server,
        login=login_info,
        password=password,
        timeout=5000,
        logger=logger,  # default is None
        ensure_trade_enabled=True,  # default is False
        enable_real_trading=True,  # default is False
        return_as_dict=False,  # default is False
        return_as_native_python_objects=False,  # default is False
    )
    with mt5_connected as conn:
        try:
            num_orders = mt5.orders_total()
            return True
        except mt5.MT5Error:
            raise


async def add_new_devs_or_modify(user: int, listener: Listener, add: bool) -> bool:
    enter_p = await aioconsole.ainput("Enter p value, separated by space\n")
    enter_tp = await aioconsole.ainput("Enter tp value, separated by space\n")
    enter_sl = await aioconsole.ainput("Enter sl value, separated by space\n")
    try:

        enter_vol = float(await aioconsole.ainput("Enter vol value >=0.01\n"))
        if enter_vol < 0.01:
            listener.logger.warning("Volume value inputted is <0.1 which is invalid for MT5 platform")
            return False
        lst_enter_p = list(map(int, enter_p.split()))
        lst_enter_tp = list(map(int, enter_tp.split()))
        lst_enter_sl = list(map(int, enter_sl.split()))
    except ValueError as e:
        listener.logger.error(f"Invalid values (strings) were inputted, please re-input")
    else:
        listener.logger.info(f"{lst_enter_p}, {lst_enter_tp}, {lst_enter_sl} {enter_vol}")
        if add == False:
            listener.const.modify_dev_config_by_dict(
                os.path.join(const_dirs.DEVS_FOLDER_CONFIG, "devs_" + str(user) + ".json"),
                lst_enter_p, lst_enter_tp, lst_enter_sl, enter_vol)
            return True
        else:
            if listener.const.add_new_dev_config(user, lst_enter_p, lst_enter_tp, lst_enter_sl, enter_vol):
                listener.logger.info(f"Successfully added dev file for user {user}")
                return True
            else:
                return False


async def fun_keypress_test(listener: Listener):
    while True:

        print("\nListening for keystroke\n"
              "1)Close all positions by symbol \n"
              "2)Close all position no matter what position is it (Specify bot type)\n"
              "3)Obtain position tickets\n"
              "4)Print the number of pending orders for each account\n"
              "5)Obtain position and magic number associated with position \n"
              "6)Print equity for each active bot\n"
              "7)Remove all pending orders\n"
              "8)Print the order history for each bot\n"
              "9)Close a random position for each bot\n"
              "10)Modify parameter devs\n"
              "11)Restart jobs and percentage check\n"
              "12)Activate percentage check variable (NO PERCENTAGE CHECK JOB)\n"
              "13)Add new bot\n"
              "14)Save data to .env\n"
              "15)Print placed orders for each account\n"
              "16)Modify percentage stop for specific bot\n"
              "17)Modify percentage stop for all the bots\n"
              "18)Stop percentage check\n"
              "19)Stop processes\n"
              "20)Deactivate a specific bot/active bots\n"
              "21)Activate a specific bot/non-active bots\n"
              "22)Reactivate bot next month\n"
              "23)Do not reactivate bot_next_month\n"
              "24)Print all the bot info: Status/Percentage_check_status/Reactivate_next_month/Percentage_stop\n")
        choice = await aioconsole.ainput()

        # if choice == 'a':
        #     for f in os.listdir(const_dirs.TEMP_DIR):
        #         path=join(const_dirs.TEMP_DIR, f)
        #         if isfile(path):
        #             processed_data=listener.get_processed_data(path)
        if choice == 'a':
            processed_data, file_path = listener.get_rand_img_and_test()
            if processed_data:
                        for bot in (bot for bot in listener.bots if bot.status.value == True):
                            bot.connect(bot.trader.trade, trade_data=processed_data)

        if choice == '1':
            symbol = await aioconsole.ainput(
                "Insert symbol in pattern:symb_pref/symb_suff or SYMB_PREF/SYMB_SUFF or SYMB_PREFSYMBSUFF or symb_prefsymb_suff\n")
            PATTERN = "([A-Z]+[\/|I][A-Z]+)"
            symbol = symbol.upper()
            match = re.match(PATTERN, symbol)
            if match:
                symbol = symbol.replace("/", "")
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                bot.connect(bot.trader.close_positions_nmw, symbol)

        elif choice == '2':
            listener.logger.info("Menu Chiusura posizioni")

            choice_sel = await aioconsole.ainput(
                "Do you want to close positions for specific bot/active/non-active/all bots?\nPossible choices: 0-1-2-3:\n")
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish to close positions\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.connect(bot.trader.close_positions_nmw)
                            break
            elif choice_sel == '1':
                lst_act_bot = [bot for bot in listener.bots if bot.status.value == True]
                if lst_act_bot:
                    for bot in lst_act_bot:
                        bot.connect(bot.trader.close_positions_nmw)
                else:
                    listener.logger.warning(
                        "It wasn't possible to close any positions because all bots statuses are set to False")
            elif choice_sel == '2':
                for bot in (bot for bot in listener.bots if bot.status.value == False):
                    bot.connect(bot.trader.close_positions_nmw)
            elif choice_sel == '3':
                for bot in listener.bots:
                    bot.connect(bot.trader.close_positions_nmw)
            else:
                listener.logger.warning("Non valid option for close position nmw was selected")


        elif choice == '3':
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                listener.logger.info(
                    f"Getting position tickets for acc: {str(bot.login)} {str(bot.connect(bot.trader.get_position_tickets))}")

        elif choice == '4':
            listener.logger.info("Printing the number of active orders for each account")
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                listener.logger.info(
                    f"Number of active orders for account {str(bot.login)} {str(bot.connect(mt5.orders_total))}")


        elif choice == '5':
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                bot.connect(bot.trader.get_tpl_magic_ticket)


        elif choice == '6':
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                listener.logger.info(f"Equity for bot {str(bot.login)} : {str(bot.connect(bot.trader.get_equity))}")

        elif choice == '7':
            listener.logger.info("Remove pending orders menu")
            choice_sel = await aioconsole.ainput(
                "Do you want to remove orders for specific bot/active/non-active/all bots?\nPossible choices: 0-1-2-3:\n")
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish to remove orders\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.connect(bot.trader.close_pending_operations)
                            break

            elif choice_sel == '1':
                lst_act_bot = [bot for bot in listener.bots if bot.status.value == True]
                if lst_act_bot:
                    for bot in lst_act_bot:
                        listener.logger.info(bot.connect(bot.trader.close_pending_operations))
                else:
                    listener.logger.warning("It wasn't possible to close any positions because all bots "
                                            "statuses are set to False")

            elif choice_sel == '2':
                for bot in (bot for bot in listener.bots if bot.status.value == False):
                    listener.logger.info(bot.connect(bot.trader.close_pending_operations))
            elif choice_sel == '3':
                for bot in listener.bots:
                    bot.connect(bot.trader.close_pending_operations)
            else:
                listener.logger.warning("Non valid option for remove all pending orders was selected")


        elif choice == '8':
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                listener.logger.info(f"History of orders for {bot.login}: {bot.connect(mt5.history_orders_get)}")

        elif choice == '9':
            for bot in (bot for bot in listener.bots if bot.status.value == True):
                random_pos = bot.connect(bot.trader.get_random_position)
                if random_pos is not None:
                    bot.connect(bot.trader.close_positions_by_id, ticket_id_rmv=random_pos)
        elif choice == '10':
            return_st, bot_login_st = await input_acc_info(listener, "Enter the account you wish to modify\n")
            if return_st:
                if any(int(bot_login_st) == bot.login for bot in listener.bots):

                    listener.logger.info(f"Modifying account {bot_login_st}\n"
                                         f"Actual devs val: {listener.const.ret_dict_from_dev(bot_login_st)}")

                    return_val = await add_new_devs_or_modify(int(bot_login_st), listener, False)
                    if not return_val:
                        listener.logger.error("An error happened during the operation you were executing")
                else:
                    listener.logger.error(f"No account was found with id {bot_login_st}")

        elif choice == '11':
            listener.scheduler_var = False
            listener.logger.info("Waiting for the percentage check to stop")
            time.sleep(2)
            listener.logger.info("Menu restart percentage check")
            possible_choices = ['0', '1', '2', '3']
            choice_sel = await aioconsole.ainput(
                "Do you want to restart percentage check for specific bot/active/non-active/all bots?\nPossible choices: 0-1-2-3:\n"
                "Keep in mind that by doing so you're going to also re-activate the bot statuses!\n")
            return_st = None
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish to restart percentage check\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.status.value = True
                            bot.freq_check.value = True
                            break
            elif choice_sel == '1':
                for bot in (bot for bot in listener.bots if bot.status.value == True):
                    bot.freq_check.value = True
            elif choice_sel == '2':
                for bot in (bot for bot in listener.bots if bot.status.value == False):
                    bot.freq_check.value = True
                    bot.freq_check.value = True
            elif choice_sel == '3':
                for bot in listener.bots:
                    bot.status.value = True
                    bot.freq_check.value = True
            else:
                listener.logger.warning("Non valid option for restart percentage_check was selected")
            if choice_sel in possible_choices and return_st == True:
                threading.Thread(target=listener.run_function_bg).start()

        elif choice=='12':
            listener.logger.info("Activate frequency check var Menu")
            choice_sel = await aioconsole.ainput(
                "Do you want to activate percentage check VARIABLE for specific bot/all bots?\nPossible choices: 0-1:\n"
                "Keep in mind that by doing so you're NOT going to ACTIVATE percentage check function!\n")

            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish to activate "
                                                               "percentage check VARIABLE\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.freq_check.value = True
                            break
            elif choice_sel == '1':
                for bot in listener.bots:
                    bot.freq_check.value=True
            else:
                listener.logger.warning("Non valid option for restart percentage VARIABLE was selected")


        elif choice == '13':

            try:
                MT_LOGIN = int(await aioconsole.ainput("Insert MT_LOGIN INFO \n"))
            except ValueError as e:
                listener.logger.error("You inserted string instead of int on MT_LOGIN_INFO")
            else:  # the else block gets executed if no error is raised
                MT_PASSWORD = await aioconsole.ainput("Insert MT_PASSWORD \n")
                MT_SERVER = await aioconsole.ainput("Insert MT_SERVER \n")
                MT_EXE_PATH = await aioconsole.ainput("Insert MT_PATH, FULL PATH\n")

                # MT_LOGIN=5457977
                # MT_PASSWORD="o8URbYYh"
                # MT_SERVER="FxPro-MT5"
                try:
                    return_cl = test_account(logger=listener.logger, status=True, login_info=MT_LOGIN,
                                             password=MT_PASSWORD,
                                             server=MT_SERVER, path=MT_EXE_PATH)
                    if return_cl:
                        new_login_info = {
                            "MT_LOGIN": MT_LOGIN,
                            "MT_SERVER": MT_SERVER,
                            "MT_PASSWORD": MT_PASSWORD,
                            "devs_path": str(os.path.join(const_dirs.DEVS_FOLDER_CONFIG, f"devs_{MT_LOGIN}.json")),
                            "MT_EXE_PATH": MT_EXE_PATH
                        }
                        if add_new_devs_or_modify(int(MT_LOGIN), listener, True):
                            time.sleep(5)
                            listener.add_new_bot(listener.logger, True, True, False, new_login_info)
                            listener.const.add_new_user(**new_login_info)

                        else:
                            listener.logger.error(f"Unable to add user {MT_LOGIN}")
                except mt5.MT5Error as e:
                    listener.logger.error(f"Error occurred {e}")
        elif choice == '14':
            listener.const.save_data_to_env_file()
        elif choice == '15':
            for bot in listener.bots:
                lst = bot.connect(mt5.orders_get)
                if lst:
                    for x in lst:
                        listener.logger.info(
                            f"Placed order {x.ticket} for account {str(bot.login)} {x}\n\n")
                else:
                    listener.logger.info(f"Couldn't get any placed order for account {str(bot.login)}")
        elif choice == '16':
            return_st, bot_login_st = await input_acc_info(listener,
                                                           "Enter the account on which you wish to modify percentage\n")
            if return_st:
                new_input = await aioconsole.ainput("Insert new percentage ")
                try:
                    new_input = float(new_input)
                except ValueError as e:
                    listener.logger.error("Percentage inserted is a string, not a float")
                else:
                    for bot in listener.bots:
                        if bot.login == int(bot_login_st):
                            bot.connect(bot.trader.change_percentage_to_meet, new_input)
                            break

        elif choice == '17':
            new_input = await aioconsole.ainput("Insert new percentage ")
            try:
                new_input = float(new_input)
            except ValueError as e:
                listener.logger.error("Percentage inserted is a string, not a float")
            else:

                for bot in listener.bots:
                    bot.connect(bot.trader.change_percentage_to_meet, new_input)


        elif choice == '18':
            listener.logger.info("Deactivate Percentage check menu")

            choice_sel = await aioconsole.ainput(
                "Do you want to stop percentage check for specific bot/active bots?\nPossible choices: 0-1:\n")
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish deactivate percentage check\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.freq_check.value = False
                            break
            elif choice_sel == '1':

                for bot in (bot for bot in listener.bots if bot.status.value == True):
                    bot.freq_check.value = False

            else:
                listener.logger.warning("Non valid option for deactivate percentage check was selected")
        elif choice == '19':
            listener.logger.info("Stopping processes")
            listener.kill_terminal_procs()
        elif choice == '20':
            listener.logger.info("Stop bot/bots Menu")
            choice_sel = await aioconsole.ainput(
                "Do you want to stop a specific bot/active bots?\nPossible choices: 0-1:\n")
            if choice_sel == '0':

                return_st, bot_login_st = await input_acc_info(listener, "Enter the account you wish to deactivate\n")
                if return_st:
                    for bot in (bot for bot in listener.bots if bot.status.value == True):
                        if bot_login_st == bot.login:
                            bot.status.value = False
                            break

            elif choice_sel=='1':
                listener.logger.info("Stopping all bots")
                for bot in (bot for bot in listener.bots if bot.status.value == True):
                    bot.status.value = False
            else:
                listener.logger.info("Non valid option for deactivate bot/bots was selected, no changes have been done.")


        elif choice == '21':
            listener.logger.info("Activate bot/bots Menu")
            choice_sel = await aioconsole.ainput(
                "Do you want to activate a specific bot/non-active bots?\nPossible choices: 0-1:\n")
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener, "Enter the account you wish to activate\n")
                if return_st:
                    for bot in (bot for bot in listener.bots if bot.status.value == False):
                        if bot_login_st == bot.login:
                            bot.status.value = True
                            break
            elif choice_sel=='1':

                listener.logger.info("Activating all bots")
                for bot in (bot for bot in listener.bots if bot.status.value == False):
                    bot.status.value = True
            else:
                listener.logger.info("Non valid option for activate bot/bots menu was selected, no changes have been "
                                     "done.")



        elif choice == '22':
            choice_sel = await aioconsole.ainput(
                "Do you want to reactivate bot next month: specific bot/all bots?\nPossible choices: 0-1:\n")
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish to change this option\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.reactivate_next_month.value = True
                            break
            elif choice_sel == '1':
                for bot in listener.bots:
                    bot.reactivate_next_month.value = True
            else:
                listener.logger.warning("Non valid option for reactivate_bot_next_month was selected")

        elif choice == '23':
            choice_sel = await aioconsole.ainput(
                "Do you want to deactivate bot next month: specific bot/all bots?\nPossible choices: 0-1:\n"
                "Remember that by doing so you're just going to activate it, but percentage check won't be performed\n"
                "on this specific bot\n")
            if choice_sel == '0':
                return_st, bot_login_st = await input_acc_info(listener,
                                                               "Enter the account on which you wish to change this option\n")
                if return_st:
                    for bot in listener.bots:
                        if bot.login == bot_login_st:
                            bot.reactivate_next_month.value = False
                            break
            elif choice_sel == '1':
                for bot in listener.bots:
                    bot.reactivate_next_month.value = False
            else:
                listener.logger.warning("Non valid option for deactivate_bot_next_month was selected")


        elif choice == '24':
            for bot in listener.bots:
                listener.logger.info(
                    f"Bot login {bot.login}, Status: {bot.status.value}, Percent_check {bot.freq_check.value}, Reactivate next month {bot.reactivate_next_month.value}, Percentage_stop {bot.trader.percentage_to_meet}")

        await asyncio.sleep(1)


def main():
    logger_instance = get_logger(name="Listener", name_file='Logger', time_utc=True)
    const_dirs_obj = const_dirs()
    const_dirs_obj.make_dir()

    listener = Listener(logger_instance)
    listener.run()

    try:
        listener.telegram.client.loop.run_until_complete(fun_keypress_test(listener))
    except KeyboardInterrupt as e:
        listener.logger.info("Exiting the program as a result of Keyboard Interrupt")
        try:
            sys.exit(-3)
        except SystemExit:
            os._exit(-3)


if __name__ == "__main__":
    main()
