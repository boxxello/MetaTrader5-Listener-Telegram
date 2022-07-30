import json

import os
import re
import sys
from datetime import datetime

from dotenv import load_dotenv

from utils import percentage_from_percent


class data_constants:
    SEP = "; "



    def __init__(self, logger):
        load_dotenv(const_dirs.USER_DATA_PATH, encoding="utf-8")
        MT_LOGIN = [int(login) for login in os.environ["MT_LOGIN"].split(self.SEP)]
        MT_SERVER = os.environ["MT_SERVER"].split(self.SEP)
        MT_PASSWORD = os.environ["MT_PASSWORD"].split(self.SEP)
        MT_EXE_PATH = os.environ["MT_EXE_PATH"].split(self.SEP)
        MINUTES_FREQUENCY_CHECK_LOG = os.environ["MINUTES_FREQUENCY_CHECK_LOG"]
        self.logger = logger
        try:
            self.MINUTES_FREQUENCY_CHECK_LOG = int(MINUTES_FREQUENCY_CHECK_LOG)
        except ValueError as e:
            self.logger.error(f".env value \"MINUTES_FREQUENCY_CHECK_LOG\" is not an integer, defaulting to 5 mins")
            self.MINUTES_FREQUENCY_CHECK_LOG=5

        DEVS_PATH = [os.path.join(
            const_dirs.DEVS_FOLDER_CONFIG, "devs_{}.json".format(login)) for login in MT_LOGIN]
        self.TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
        self.TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]
        self.CHANNEL_NAME = os.environ["CHANNEL_NAME"]
        self.SESSION_NAME = os.environ["SESSION_NAME"]

        self.devs_path = DEVS_PATH

        try:
            self.mt_data = [{
                "MT_LOGIN": MT_LOGIN[i],
                "MT_SERVER": MT_SERVER[i],
                "MT_PASSWORD": MT_PASSWORD[i],
                "devs_path": DEVS_PATH[i],
                "MT_EXE_PATH": MT_EXE_PATH[i]
            } for i in range(len(MT_LOGIN))]
        except IndexError as e:
            self.logger.error(f"Check .env file {const_dirs.USER_DATA_PATH},"
                              f"number of accounts is {len(MT_LOGIN)} based on MT_LOGIN: "
                              f"not all required info was provided")
            sys.exit(-10)


    def add_new_user(self, MT_LOGIN: int, MT_PASSWORD: str, MT_SERVER: str, MT_EXE_PATH: str, devs_path: str):
        self.mt_data.append({
            "MT_LOGIN": MT_LOGIN,
            "MT_SERVER": MT_SERVER,
            "MT_PASSWORD": MT_PASSWORD,
            "devs_path": devs_path,
            "MT_EXE_PATH": MT_EXE_PATH
        })

    def save_data_to_env_file(self, file_path="user_data.env"):
        """
        Not used because it redirected sysout to file.
        What happens here is:
        
        The original file is moved to a backup file
        The standard output is redirected to the original file in the loop
        Any print statement gets wrote back into the original file
        """

        # for x in self.mt_data:
        #     print(self.mt_data)
        # for i in range(1,2):
        #     for key in self.mt_data[1]:
        #         print(str([ti[key] for ti in self.mt_data]).replace("[", "").replace("]", "").replace(
        #                                ",", ";").replace("'", ""))

        # _temp_flag = True
        # with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        #     for line in file:
        #         _temp_flag = False
        #         for key in self.mt_data[1]:
        #             if line.startswith(key):
        #                 print(line.replace(line.partition("=")[2],
        #                                    str([ti[key] for ti in self.mt_data]).replace("[", "").replace("]",
        #                                                                                                   "").replace(
        #                                        ",", ";").replace("'", "")), end="\n")
        #                 _temp_flag = True
        #                 break
        #         if _temp_flag is False:
        #             print(line.rstrip())

        _temp_flag = True
        content: list[str]
        try:
            with open(file_path, "r") as file:
                content = file.readlines()
        except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
            self.logger.error("Error while reading file content, aborting")
            return
        try:
            with open(file_path, "w+") as file:
                print(f"Content in file {content}")
                for line in content:

                    _temp_flag = False
                    for key in self.mt_data[1]:
                        if line.startswith(key):
                            file.write(line.replace(line.partition("=")[2],
                                                    str([ti[key] for ti in self.mt_data]).replace("[", "").replace("]",
                                                                                                                   "").replace(
                                                        ",", ";").replace("'", "") + "\n"))
                            _temp_flag = True
                            break
                    if _temp_flag is False:
                        file.write(line)
            self.logger.info("Successfully saved data to the .env file")
        except EnvironmentError:
            self.logger.error("Error while writing data do .env file, aborting")

    def add_new_dev_config(self, user: int, p: list, tp: list, sl: list, vol: float):
        global base_path

        lst_lists = [p, tp, sl]
        file_name = os.path.join(const_dirs.DEVS_FOLDER_CONFIG, f"devs_{user}.json")
        base_path = os.path.basename(os.path.normpath(file_name))
        if not os.path.exists(file_name):
            self.logger.info(f"loading {base_path}")
            if all(len(x) == 2 for x in lst_lists) and vol >= 0.01:

                devs_dict = {'p': p,
                             'sl': sl,
                             'tp': tp,
                             'vol': vol
                             }
                with open(file_name, "w") as file:
                    json.dump(devs_dict, file, indent=4, sort_keys=True)
                self.logger.info(f"Dev file added {base_path}")
                return True
            else:
                self.logger.error(f"Devs file paramaters for file {base_path} are incorrect")
                return False

        else:
            self.logger.error(f"{base_path} already exists in {const_dirs.DEVS_FOLDER_CONFIG}")
            return False

    def ret_dict_from_dev(self, user=None, file_name=None) -> tuple:
        if user is None and file_name is None:
            self.logger.error("Both user and filepath are none")
            return ()

        # pattern="^devs_\d{5,}\.json$"
        # not needed anymore
        if file_name is None:
            for string in self.devs_path:
                base_path = os.path.basename(os.path.normpath(string))
                self.logger.debug(repr(base_path))
                if re.search(rf"^devs_{user}\.json$", base_path):

                    try:
                        with open(string, 'r') as f:
                            devs_obj = json.load(f)
                    except IOError as e:
                        self.logger.error(f"I/O error({e.errno}): {e.strerror}")
                        return ()
                    except:
                        self.logger.error("Unexpected error:", sys.exc_info()[0])
                        return ()
                    self.logger.debug(f"loading {base_path}")
                    return devs_obj, base_path
            self.logger.error(f"Unable to find file devs_{user}.json")

        else:
            for string in self.devs_path:
                base_path = os.path.basename(os.path.normpath(string))

                if file_name == base_path:
                    try:
                        with open(string, 'r') as f:
                            devs_obj = json.load(f)
                    except IOError as e:
                        self.logger.error(f"I/O error({e.errno}): {e.strerror}")
                        return ()
                    except:
                        self.logger.error("Unexpected error:", sys.exc_info()[0])
                        return ()
                    self.logger.debug(f"loading {base_path}")
                    return devs_obj, base_path
            self.logger.error(f"Unable to find file {file_name}")

    def modify_dev_config_by_dict(self, file_path, p: list = None, tp: list = None, sl: list = None,
                                  vol: float = None) -> dict:
        try:

            with open(file_path, 'r') as f:
                devs_obj = json.load(f)
        except IOError as e:
            self.logger.error(f"I/O error({e.errno}): {e.strerror}")
            return {}
        except:
            self.logger.error("Unexpected error:", sys.exc_info()[0])
            return {}
        info_string = f"List of params that got changed in file {file_path}"
        if p is not None and len(p) == 2:
            devs_obj["p"] = p
            info_string += f" p: {p} "
        if tp is not None and len(tp) == 2:
            devs_obj["tp"] = tp
            info_string += f"tp: {tp} "
        if sl is not None and len(sl) == 2:
            devs_obj["sl"] = sl
            info_string += f"sl: {sl} "
        if vol is not None and vol >= 0.01:
            devs_obj["vol"] = vol
            info_string += f"vol: {vol} "
        try:
            with open(os.path.join(const_dirs.DEVS_FOLDER_CONFIG, file_path), "w") as file:
                json.dump(devs_obj, file, indent=4, sort_keys=True)
        except IOError as e:
            self.logger.error(f"OOPS! I/O error({e.errno}): {e.strerror}")
            return {}
        self.logger.debug(info_string)
        return devs_obj

    def modify_vol_from_percentage(self, user: int, percentage: float) -> dict:
        devs_obj, name_file = self.ret_dict_from_dev(user)
        actual_volume = devs_obj["vol"]
        recalc_volume = round((percentage_from_percent(percentage, actual_volume)) + actual_volume, 2)
        devs_obj["vol"] = recalc_volume
        for x in self.devs_path:
            base_path = os.path.basename(os.path.normpath(x))
            if base_path==name_file:
                return self.modify_dev_config_by_dict(x, **devs_obj)


class const_dirs:
    CURR_DIR = os.path.dirname(__file__)
    USER_DATA_PATH = os.path.join(CURR_DIR, "user_data.env")
    TEMP_DIR = os.path.join(CURR_DIR, "temp")
    LOG_DIR = os.path.join(CURR_DIR, "logs")
    DEVS_FOLDER_CONFIG = os.path.join(CURR_DIR, "devs_config_files")
    load_dotenv(USER_DATA_PATH, encoding="utf-8")
    TESSERACT_PATH = os.environ["TESSERACT_PATH"]
    LOG_FILE_SUFFIX = ('_{}.log'.format(datetime.now().strftime("%d_%m_%Y__%H_%M_%S")))

    def __init__(self):
        pass

    def make_dir(self):
        dir_list = {self.LOG_DIR, self.TEMP_DIR}

        for dir in dir_list:
            if not os.path.isdir(dir):
                try:
                    os.makedirs(dir)
                except OSError as e:
                    print(f"Unable to create {dir}, exception was thrown {e.strerror}")
                    sys.exit(-4)