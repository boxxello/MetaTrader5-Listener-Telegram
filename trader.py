import math
from datetime import datetime, timedelta
import json
import random
import sys

import pymt5adapter as mt5
from utils import count_decimals, percentage, percentage_from_percent, last_day_of_month, last_day_of_previous_month


class Trader:
    def __init__(self, devs_path, logger):
        self.logger = logger
        self.devs_path = devs_path
        self.percentage_to_meet = float(200)
        try:
            with open(devs_path) as f:
                self.devs = json.load(f)
        except FileNotFoundError:

            self.logger.error(f"A dev file: {devs_path} wasn't found, exiting")
            sys.exit(-1)

    def reload_devs(self):
        with open(self.devs_path) as f:
            self.devs = json.load(f)

    def is_terminal_up(self):
        self.logger.info("Terminal is up and running")
    def market_order(self, symbol, order_type, tp, sl):
        self.logger.debug("Starting funct market_order")
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(self.devs["vol"]),
            "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
            "tp": tp,
            "sl": sl,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        order = mt5.order_send(request)
        if order.retcode != mt5.TRADE_RETCODE_DONE:
            retcode, comment = order.retcode, order.comment
            self.logger.error(
                f"Error sending market {order_type} order {request}: {retcode, comment}")
        else:
            self.logger.info(f"Market {order_type} order {request} sent successfully.")
        return request

    def pending_order(self, symbol, order_type, price, tp, sl, bid, ask, volume=None):
        self.logger.debug("Starting funct pending_order")

        if order_type == "buy":
            if ask > price:
                typ = mt5.ORDER_TYPE_BUY_LIMIT
            else:
                typ = mt5.ORDER_TYPE_BUY_STOP
        else:
            if bid < price:
                typ = mt5.ORDER_TYPE_SELL_LIMIT
            else:
                typ = mt5.ORDER_TYPE_SELL_STOP
        if typ in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT]:
            typ_label = "limit"
        else:
            typ_label = "stop"
        if volume is None:
            volume = float(self.devs["vol"])
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "type": typ,
            "tp": tp,
            "sl": sl,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        order = mt5.order_send(request)

        if order.retcode != mt5.TRADE_RETCODE_DONE:
            retcode, comment = order.retcode, order.comment
            self.logger.error(
                f"Error sending pending {order_type} {typ_label} order {request}: {retcode, comment}")
        else:
            self.logger.info(f"Pending {order_type} {typ_label} order {request} was sent successfully.")

    def get_symbol_info(self, symbol):
        self.logger.debug("Starting funct get_symbol_info")
        while True:
            info = mt5.symbol_info_tick(symbol)
            if info and info.time != 0:
                break
        return info, mt5.symbol_info(symbol)

    def add_symbol(self, symbol, second_try=False):
        if not mt5.symbol_select(symbol, True):
            error = mt5.last_error()
            self.logger.error(f"Couldn't add symbol {symbol}: {error}")
            if not second_try:
                return self.add_symbol(symbol[:-1], second_try=True)
            return False
        self.logger.info(f"Added {symbol} to Market Watch.")
        return symbol

    def trade(self, trade_data):
        self.logger.debug("Starting funct trade")
        symbol = trade_data["symbol"] + "."
        added_symbol = self.add_symbol(symbol=symbol)

        if not added_symbol: return

        symbol_info_tick, symbol_info = self.get_symbol_info(symbol=added_symbol)

        bid, ask = symbol_info_tick.bid, symbol_info_tick.ask
        stops_level = symbol_info.trade_stops_level / (10 ** symbol_info.digits)
        self.logger.info(f"Current {added_symbol} prices: bid {bid:.5f}, ask {ask:.5f}")
        self.logger.info(f"Stops level: {stops_level}")

        order_type = trade_data["type"]
        price = trade_data["price"]
        decimals = count_decimals(price)
        price = float(price)
        tp1 = float(trade_data["tp1"])
        tp2 = float(trade_data["tp2"])
        tp3 = float(trade_data["tp3"])
        sl = float(trade_data["sl"])

        index = 0 if order_type == "buy" else 1
        padd = self.devs["p"][index]
        tpadd = self.devs["tp"][index]
        sladd = self.devs["sl"][index]

        pip_val = 0.0001 if decimals > 2 else 0.01

        p = ((tp2 + tp3) / 2) + padd * pip_val
        tp = tp3 + tpadd * pip_val
        sl = tp2 + sladd * pip_val
        sig = -1 if order_type == "sell" else 1
        if abs(p - tp) < stops_level:
            tp = p + stops_level * sig
        if abs(p - sl) < stops_level:
            sl = p + stops_level * sig * -1

        self.pending_order(
            added_symbol,
            order_type,
            round(p, 5),
            round(tp, 5),
            round(sl, 5),
            bid, ask
        )



    def get_position_tickets(self, symbol=None):
        list = []
        if symbol is not None:
            open_positions = mt5.positions_get(symbol=symbol)
        else:
            open_positions = mt5.positions_get()
        for x in open_positions:
            list.append(x.ticket)
        return list

    def close_positions_by_id(self, ticket_id_rmv, comment=None):
        global chosen_position
        open_positions = mt5.positions_get()
        if len(open_positions) > 0:
            try:
                chosen_position = next(i for i in open_positions if i.ticket == ticket_id_rmv)
            except StopIteration as e:
                self.logger.warning(f"No positions to remove were found for account: {mt5.account_info().login}")
                return
            order_type = chosen_position.type
            ticket = chosen_position.ticket
            symbol = chosen_position.symbol
            volume = chosen_position.volume

            if comment is None:
                comment = "Close trade id"
            if order_type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type,
                "position": ticket,
                "price": price,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(close_request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(
                    "Position to close order: Ticket ID: {}, Encountered Error {} , Return code {}".format(ticket,
                                                                                                           mt5.last_error(),
                                                                                                           result.retcode))
            else:
                self.logger.info(f"Position successfully closed! Ticket ID: {ticket}")

            return ticket, result.retcode

    def close_positions_nmw(self, symbol: str = None, comment=None) -> list:
        lst_tuple = list(zip())

        global chosen_position
        if symbol is None:
            open_positions = mt5.positions_get()
        else:
            open_positions = mt5.positions_get(symbol=symbol)

        if len(open_positions) > 0:
            for i in range(len(open_positions)):
                chosen_position = open_positions[i]
                order_type = chosen_position.type
                ticket = chosen_position.ticket
                symbol = chosen_position.symbol
                volume = chosen_position.volume

                if comment is None:
                    comment = "Close trade nmw"
                if order_type == mt5.ORDER_TYPE_BUY:
                    order_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(symbol).bid
                else:
                    order_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(symbol).ask

                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": float(volume),
                    "type": order_type,
                    "position": ticket,
                    "price": price,
                    "magic": 234000,
                    "comment": comment,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(close_request)

                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    self.logger.error(
                        f"Position to close order: Ticket ID: {ticket}, Encountered Error {mt5.last_error()} , Return code {result.retcode}")

                else:
                    self.logger.info(f"Position successfully closed! Ticket ID: {ticket}")

                lst_tuple.append(tuple((ticket, result.retcode)))
        else:
            if symbol is None:
                self.logger.warning(f"No positions to remove were found for account: {mt5.account_info().login}")
            else:
                self.logger.warning(
                    f"No positions to remove with symbol {symbol} were found for account: {mt5.account_info().login}")

        return lst_tuple

    def close_pending_operations(self):
        lst_tuple = list(zip())
        global chosen_position
        pending_orders = mt5.mt5_orders_get()

        if len(pending_orders) > 0:
            for i in range(len(pending_orders)):

                chosen_position = pending_orders[i]
                order_type = chosen_position.type
                ticket = chosen_position.ticket
                symbol = chosen_position.symbol
                volume = chosen_position.volume_initial

                close_request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "symbol": symbol,
                    "type": order_type,
                    "order": ticket,
                    "magic": 234000,
                    "volume": volume,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.mt5_order_send(close_request)

                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    self.logger.error(
                        f"Failed to close order for account {mt5.account_info().login} Deal ID: {ticket}, Encountered Error {mt5.mt5_last_error()} , Return code {result.retcode}")
                else:
                    self.logger.info(
                        f"Order successfully closed! Deal ID: {ticket} for account {mt5.account_info().login} ")
                lst_tuple.append(tuple((ticket, result.retcode)))
        else:

            self.logger.warning(f"No pending orders to remove were found for account: {mt5.account_info().login}")
        return lst_tuple

    def get_tpl_magic_ticket(self, symbol=None):
        lst_tuple = list(zip())
        tempflag = False
        if symbol is None:
            symbol_positions = mt5.positions_get()
            tempflag = True
        else:
            symbol_positions = mt5.positions_get(symbol)
        if symbol_positions is None or symbol_positions == 0 or symbol_positions == ():
            if not tempflag:
                self.logger.warning(f"No positions with symbol=\"{symbol}\"")
            else:
                self.logger.warning(f"No positions were found for account: {mt5.account_info().login}")
        elif len(symbol_positions) > 0:

            lst = list(symbol_positions)
            for pos in lst:
                lst_tuple.append(tuple((pos.ticket, pos.magic)))

            for k, b in lst_tuple:
                self.logger.info(
                    f"Position with Magic number: {b} and Ticket_No: {k} in account:  {mt5.account_info().login}")

            return lst_tuple

    def get_equity(self):
        account_info = mt5.account_info()
        if account_info is not None:
            account_info_dict = mt5.account_info()._asdict()
            return account_info_dict['equity']

    def get_random_position(self):
        lst_open_pos = mt5.positions_get()
        lst_tickets_open_pos = [x.ticket for x in lst_open_pos if len(lst_open_pos) > 0]
        if (len(lst_tickets_open_pos) > 0):
            random_pos = random.choice(lst_tickets_open_pos)
            self.logger.info(f"random pos: {random_pos}")
            return random_pos
        self.logger.error(f"Could not find any open position for acc {mt5.account_info().login}")

    def check_history_equity(self, days_to_sub=None):

        today = datetime.today()
        today_date = datetime(today.year, today.month, today.day)
        if days_to_sub is None:
            old_date_d = last_day_of_previous_month()
            old_date = datetime.combine(old_date_d, datetime.min.time())

        else:
            old_date = (today_date - timedelta(days_to_sub))
        actual_balance = mt5.account_info().equity
        old_old_date = datetime(1971, 1, 1)

        trades_lst_from_old = mt5.mt5_history_deals_get(old_old_date, old_date)
        bal_from_zero = 0
        if trades_lst_from_old:
            for a in trades_lst_from_old:
                bal_from_zero += a.profit
                bal_from_zero += a.swap
                bal_from_zero += a.commission

        amount_during_month = 0
        trades_during_month = mt5.mt5_history_deals_get(old_date, today)
        if trades_during_month:
            for a in trades_during_month:
                if a.type==mt5.DEAL_TYPE_BALANCE:
                    amount_during_month += a.profit

        delta_balance = actual_balance - bal_from_zero - amount_during_month

        if bal_from_zero != 0:
            perc = percentage(delta_balance, bal_from_zero)
            rounded_percentage = round(perc, 3)

            return rounded_percentage
        else:
            return 0
    # def check_percentage_allowance(self, days_to_sub=None):
    #
    #     percentage_history = self.check_history_equity(days_to_sub)
    #     if percentage_history > 0:
    #         lst_tuple = self.check_pos_cost()
    #         tot_amount: int = 0
    #         for k, v in lst_tuple:
    #             tot_amount += v
    #         tot_amount_percent = percentage_from_percent(percentage_history, tot_amount)
    #
    #         return (-1, percentage_history) if mt5.account_info().balance < tot_amount_percent else (
    #             1, percentage_history)
    #     else:
    #         return 0, percentage_history






    def change_percentage_to_meet(self, percentage_to_meet: float):
        self.percentage_to_meet = round(percentage_to_meet, 2)
        self.logger.info(f"Sucessfully changed percentage to {self.percentage_to_meet}")

    def frequency_check_trade(self, tolerance: float = 0.5, days_to_sub=None):

        percentage_history = self.check_history_equity(days_to_sub)

        if math.isclose(percentage_history, self.percentage_to_meet, abs_tol=tolerance) or \
                percentage_history >= self.percentage_to_meet:

            open_positions = mt5.positions_get()
            if len(open_positions) > 0:
                self.close_positions_nmw()
            return False, mt5.account_info().login, percentage_history, self.percentage_to_meet
        else:
            return True, mt5.account_info().login, percentage_history, self.percentage_to_meet

    # def augment_all_open_trades(self, days_to_sub=None):
    #     self.logger.debug("Starting augument all open trades funct")
    #     return_st, percentage_history = self.check_percentage_allowance(days_to_sub)
    #
    #     if return_st == 1:
    #
    #         lst_tuple = list(zip())
    #
    #         global chosen_position
    #         open_positions = mt5.positions_get()
    #         if len(open_positions) > 0:
    #             for i in range(len(open_positions)):
    #                 chosen_position = open_positions[i]
    #
    #                 self.logger.info(chosen_position)
    #
    #                 symbol = chosen_position.symbol
    #                 ticket = chosen_position.ticket
    #                 order_type = chosen_position.type
    #                 volume = chosen_position.volume
    #                 tp = chosen_position.tp
    #                 sl = chosen_position.sl
    #                 ticket_prev, retcode_prev = self.close_positions_by_id(ticket)
    #                 if retcode_prev == mt5.TRADE_RETCODE_DONE:
    #                     recalc_volume = round((percentage_from_percent(percentage_history, volume)) + volume, 2)
    #                     self.logger.debug(f"Recalculated volume {recalc_volume}, Previous volume: {volume}")
    #                     if order_type == mt5.ORDER_TYPE_BUY:
    #                         price = mt5.symbol_info_tick(symbol).ask
    #                     else:
    #                         price = mt5.symbol_info_tick(symbol).bid
    #                         # order = mt5.order_send(action=mt5.TRADE_ACTION_PENDING, symbol=symbol, type=order_type,
    #                         #                        price=price, sl=sl, tp=tp, type_filling=mt5.ORDER_FILLING_IOC,
    #                         #                        type_time=mt5.ORDER_TIME_GTC, volume=float(recalc_volume))
    #                         # order = mt5.order_send(action=mt5.TRADE_ACTION_DEAL, symbol=symbol, type=order_type,
    #                         #                        price=price, type_filling=mt5.ORDER_FILLING_IOC,
    #                         #                        type_time=mt5.ORDER_TIME_GTC, volume=float(recalc_volume))
    #                     modify_order_request = {
    #                         "action": mt5.TRADE_ACTION_DEAL,
    #                         "symbol": symbol,
    #                         "type": order_type,
    #                         "price": price,
    #                         "tp": tp,
    #                         "sl": sl,
    #                         "volume": float(recalc_volume),
    #                         "type_time": mt5.ORDER_TIME_GTC,
    #                         "type_filling": mt5.ORDER_FILLING_IOC,
    #                     }
    #                     self.logger.info(modify_order_request)
    #
    #                     order = mt5.order_send(modify_order_request)
    #
    #                     if order.retcode != mt5.TRADE_RETCODE_DONE:
    #                         self.logger.error(
    #                             f"Error sending modify request for order {ticket} {modify_order_request}: {order.retcode} comment: {order.comment}")
    #                     else:
    #                         self.logger.info(f"Succesfully modified order {ticket} order {modify_order_request}")
    #                     lst_tuple.append((ticket, order.retcode))
    #                 else:
    #                     self.logger.error(f"Unable to close position: {ticket_prev} to augment")
    #             return lst_tuple
    #     elif return_st == -1:
    #         self.logger.warning(f"History deals percentage profit is > 0, but acc balance doesn't allow it")
    #         return False
    #     elif return_st == 0:
    #         self.logger.warning(f"History deals percentage profit is < 0")
    #         return False

    def check_pos_cost(self):
        lst_tuple = list(zip())

        global chosen_position
        open_positions = mt5.positions_get()
        if len(open_positions) > 0:
            for i in range(len(open_positions)):
                chosen_position = open_positions[i]
                ticket = chosen_position.ticket
                symbol = chosen_position.symbol
                volume = chosen_position.volume
                price = mt5.symbol_info_tick(symbol).ask

                buy_cost = round(volume * price, 3)

                lst_tuple.append(tuple((ticket, buy_cost)))

        return lst_tuple
