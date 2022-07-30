import os

import psutil


class Executable:
    def __init__(self):
        pass

    @staticmethod
    def check_running_program(list_executables_to_check: list) -> tuple:
        new_list_base = [os.path.basename(os.path.normpath(exec)) for exec in list_executables_to_check]
        success_list = []
        unable_lst = []
        found_proc_lst = []
        my_pid = os.getpid()

        for exec in new_list_base:
            for p in psutil.process_iter():
                if p.name() == exec:
                    found_proc_lst.append(exec)
                    if not p.pid == my_pid:
                        try:
                            p.terminate()
                            success_list.append(p.name())
                        except psutil.AccessDenied:
                            unable_lst.append(p.name())
        return success_list, unable_lst, found_proc_lst

    @staticmethod
    def check_are_all_terminals_running(list_executables_to_check: list) -> list:
        new_list_base = [os.path.basename(os.path.normpath(exec)) for exec in list_executables_to_check]

        found_proc_lst = []

        for exec in new_list_base:
            for p in psutil.process_iter():
                if p.name() == exec and p.pid not in found_proc_lst:
                    found_proc_lst.append(p.pid)

        return found_proc_lst
