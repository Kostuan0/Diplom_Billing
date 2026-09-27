from PyQt5 import QtCore, QtGui, QtWidgets
from functions import *


class CheckThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def thr_reg_dogovor(self, cntr_number, first_name, second_name):
        create_dogovor(cntr_number, first_name, second_name, self.mysignal)  # вызов функции из functions

    def thr_reg_user(self, user_login, user_name, user_password, user_email, contract_number, tariff_name,
                     user_balance):
        insert_user(user_login, user_name, user_password, user_email, contract_number, tariff_name, user_balance,
                    self.mysignal)

    def thr_reg_tariff(self, tariff_name, tariff_limit, tariff_description, tariff_price_per_month):
        insert_tariff(tariff_name, tariff_limit,  tariff_description, tariff_price_per_month)


    def thr_check_tariff(self, tariff_name):
        check_tariff_exist(tariff_name)
        result = check_tariff_exist(tariff_name)
        return result
