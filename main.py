import contextlib

from PyQt5.QtWidgets import QTableWidgetItem
from loguru import logger
import sys
from bd_form import *
from check_db import *
import functions


class Interface(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.check_db = CheckThread()
        self.check_db.mysignal.connect(self.signal)

        #кнопки
        self.ui._btn_w_contract.clicked.connect(self.reg_dogovor)
        self.ui._btn_w_reg_user.clicked.connect(self.reg_user)
        self.ui._btn_w_users_operations.clicked.connect(self.get_user_operations)
        self.ui._btn_w_tariff_add.clicked.connect(self.reg_tariff)
        self.ui._box_w_tariff.currentTextChanged.connect(self.insert_info_tariff)
        self.ui._box_w_pull.currentTextChanged.connect(self.get_ip_pull)


        self.select_users_data()
        self.insert_combo_box()
        self.ui._user_table.setFixedWidth(400)
        self.ui._user_table.setColumnWidth(0, 400)
        self.ui._operation_table.setFixedWidth(700)

        #нажатие на таблицу с юзерами
        self.ui._user_table.cellClicked[int, int].connect(self.click_on_user)

    def get_ip_pull(self, value):
        pull_ip_name = self.ui._box_w_pull.currentText()
        cur = con.cursor()
        sql_get_ip_pull = f"SELECT IP_ADDRESS, IP_PULL, IP_STATUS FROM ip_table " \
                          f"WHERE IP_PULL = '{pull_ip_name}'"
        cur.execute(sql_get_ip_pull)
        rez_ip_pull = cur.fetchall()
        len_rez_ip_pull = len(rez_ip_pull)
        self.ui._ip_pull_table.setRowCount(len_rez_ip_pull)
        self.ui._ip_pull_table.setColumnCount(3)
        self.ui._ip_pull_table.setColumnWidth(0, 450)
        self.ui._ip_pull_table.setColumnWidth(1, 700)
        self.ui._ip_pull_table.setColumnWidth(2, 600)
        self.ui._ip_pull_table.setHorizontalHeaderLabels(('IP', 'Название пула', 'Статус адреса'))
        row_number = 0
        for pull in rez_ip_pull:
            self.ui._ip_pull_table.setItem(row_number, 0, QTableWidgetItem(pull['IP_ADDRESS']))
            self.ui._ip_pull_table.setItem(row_number, 1, QTableWidgetItem(pull['IP_PULL']))
            if pull['IP_STATUS'] != 0:
                self.ui._ip_pull_table.setItem(row_number, 2, QTableWidgetItem('Занят'))
            else:
                self.ui._ip_pull_table.setItem(row_number, 2, QTableWidgetItem('Свободен'))
            row_number += 1
        cur.close()
        print(value)


    #вставка тарифа и выбор уже существующего для просмотра инфы о нём
    @logger.catch
    def insert_info_tariff(self, value):
        tariff_name = self.ui._box_w_tariff.currentText()
        cur = con.cursor()
        sql_get_tariff = f"SELECT * FROM tariff " \
                         f"WHERE TARIFF_NAME = '{tariff_name}'"
        cur.execute(sql_get_tariff)
        rez_tariff = cur.fetchall()
        self.ui._le_w_tariff_name.setText(rez_tariff[0]['TARIFF_NAME'])
        self.ui._le_w_tariff_speed.setText(str(rez_tariff[0]['TARIFF_LIMIT']))
        self.ui._le_w_tariff_price_m.setText(str(rez_tariff[0]['TARIFF_PRICE_PER_MONTH']))
        self.ui._le_w_tariff_description.setText(rez_tariff[0]['TARIFF_DESCRIPTION'])
        print(value)


    #регистрация тарифа
    @logger.catch
    def reg_tariff(self, value):
        try:
            tariff_name = self.ui._le_w_tariff_name.text()
            tariff_limit = self.ui._le_w_tariff_speed.text()
            tariff_price_per_month = self.ui._le_w_tariff_price_m.text()
            tariff_description = self.ui._le_w_tariff_description.text()
            tariff_check = (self.check_db.thr_check_tariff(tariff_name))
            if (len(tariff_name) != 0 and len(tariff_limit) != 0 and len(tariff_price_per_month) != 0
                    and len(tariff_description) != 0 and tariff_check == "No"):
                self.check_db.thr_reg_tariff(tariff_name, tariff_limit, tariff_description, tariff_price_per_month)
                self.signal('Тариф успешно введён')
                self.ui._le_w_tariff_name.clear()
                self.ui._le_w_tariff_speed.clear()
                self.ui._le_w_tariff_price_m.clear()
                self.ui._le_w_tariff_description.clear()
            else:
                self.signal('Заполните все поля или измените название тарифа')
            print(value)
        except Exception as ex:
            print(ex)

    #ввод комбо-боксов тарифов и пул-нейма
    @logger.catch
    def insert_combo_box(self):
        cur = con.cursor()
        sql_get_tariff = "SELECT TARIFF_NAME FROM tariff"
        cur.execute(sql_get_tariff)
        rez_tariff_name = cur.fetchall()
        for tariff_name in rez_tariff_name:
            self.ui._box_reg_user_tariff_name.addItem(tariff_name['TARIFF_NAME'])
            self.ui._box_w_tariff.addItem(tariff_name['TARIFF_NAME'])
        sql_get_pull_ip = "SELECT PULL_NAME FROM ip_pull"
        cur.execute(sql_get_pull_ip)
        rez_pull_name = cur.fetchall()
        for ip_name in rez_pull_name:
            self.ui._box_w_pull.addItem(ip_name['PULL_NAME'])
        cur.close()

    #при нажатии на кнопку операции выводит операции пользователя
    @logger.catch
    def get_user_operations(self, value_button):
        user_login = self.ui._le_w_users_login.text()
        if len(user_login) != 0:
            cur = con.cursor()
            sql_get_user_operations = f"SELECT USER_LOGIN, OPERATION_SUM, OPERATION_DATA, " \
                                      f"OPERATION_OSTATOK, OPERATION_TYPE " \
                                      f"FROM operations " \
                                      f"WHERE USER_LOGIN = '{user_login}'"
            cur.execute(sql_get_user_operations)
            rez_operation = cur.fetchall()
            len_rez_operation = len(rez_operation)
            self.ui._operation_table.setRowCount(len_rez_operation)
            self.ui._operation_table.setColumnCount(5)
            self.ui._operation_table.setColumnWidth(0, 250)
            self.ui._operation_table.setColumnWidth(1, 120)
            self.ui._operation_table.setColumnWidth(2, 350)
            self.ui._operation_table.setColumnWidth(3, 150)
            self.ui._operation_table.setColumnWidth(4, 200)
            self.ui._user_table.setHorizontalHeaderLabels(('Логин', 'Сумма', 'Дата операции', 'Остаток счёта', 'Тип операции'))
            row_number = 0
            for operation in rez_operation:
                self.ui._operation_table.setItem(row_number, 0, QTableWidgetItem(operation['USER_LOGIN']))
                self.ui._operation_table.setItem(row_number, 1, QTableWidgetItem(str(operation['OPERATION_SUM'])))
                self.ui._operation_table.setItem(row_number, 2, QTableWidgetItem(str(operation['OPERATION_DATA'])))
                self.ui._operation_table.setItem(row_number, 3, QTableWidgetItem(str(operation['OPERATION_OSTATOK'])))
                self.ui._operation_table.setItem(row_number, 4, QTableWidgetItem(str(operation['OPERATION_TYPE'])))
                row_number+=1
            cur.close()
            print(value_button)

        else:
            self.signal('Выберите пользователя')

    #вывод пользователей в таблицу
    @logger.catch
    def select_users_data(self):
        cur = con.cursor()
        sql_get_users = "SELECT USER_LOGIN FROM users"
        cur.execute(sql_get_users)
        rez_user = cur.fetchall()
        len_users = len(rez_user)
        self.ui._user_table.setRowCount(len_users)
        self.ui._user_table.setColumnCount(1)
        self.ui._user_table.setHorizontalHeaderLabels(('Пользователи', 'Пользователи'))
        row_number = 0
        for users in rez_user:
            self.ui._user_table.setItem(row_number, 0, QTableWidgetItem(users['USER_LOGIN']))
            row_number+=1
        cur.close()

    #функция отправки сигнала при совершении действия
    def signal(self, value):
        QtWidgets.QMessageBox.about(self, 'Оповещение', value)

    #регистрация договора через форму
    @logger.catch
    def reg_dogovor(self, value_button):
        cntr_number = self.ui._le_w_contract_number.text()
        first_name = self.ui._le_w_contract_first_name.text()
        second_name = self.ui._le_w_contract_second_name.text()
        self.check_db.thr_reg_dogovor(cntr_number, first_name, second_name)
        print(value_button)
        self.ui._le_w_contract_number.clear()
        self.ui._le_w_contract_first_name.clear()
        self.ui._le_w_contract_second_name.clear()

    #регистрация юзера через форму
    @logger.catch
    def reg_user(self, value_button):
        user_login = self.ui._le_w_reg_user_login.text()
        user_name = self.ui._le_w_reg_user_name.text()
        user_password = self.ui._le_w_reg_user_password.text()
        user_email = self.ui._le_w_reg_user_mail.text()
        contract_number = self.ui._le_w_reg_user_cnt_number.text()
        tariff_name = self.ui._box_reg_user_tariff_name.currentText()
        user_balance = self.ui._le_w_reg_user_balance.text()
        self.check_db.thr_reg_user(user_login, user_name, user_password, user_email, contract_number, tariff_name, user_balance)
        print(value_button)
        self.ui._le_w_reg_user_login.clear()
        self.ui._le_w_reg_user_name.clear()
        self.ui._le_w_reg_user_password.clear()
        self.ui._le_w_reg_user_mail.clear()
        self.ui._le_w_reg_user_cnt_number.clear()
        self.ui._le_w_reg_user_balance.clear()
        self.select_users_data()

    #при клике на юзера в таблицу отображается информация о нём в полях
    @logger.catch
    def click_on_user(self, row, column):
        row = self.ui._user_table.currentRow()
        column = self.ui._user_table.currentColumn()
        get_user = self.ui._user_table.item(row, column).text()
        cur = con.cursor()
        select_user_info = f"SELECT u.USER_LOGIN, u.USER_NAME, u.USER_PASSWORD, u.USER_EMAIL, u.CONTRACT_NUMBER, " \
                           f"u.USER_BALANCE, u.TARIFF_NAME, u.USER_IP, u.USER_STATUS, p.PULL_NAME " \
                           f"FROM users u " \
                           f"JOIN tariff t ON u.TARIFF_NAME = t.TARIFF_NAME " \
                           f"JOIN ip_pull p ON t.TARIFF_NAME = p.TARIFF_NAME " \
                           f"WHERE u.USER_LOGIN = '{get_user}'"
        cur.execute(select_user_info)
        rez_user_info = cur.fetchall()
        self.ui._le_w_users_login.setText(rez_user_info[0]['USER_LOGIN'])
        self.ui._le_w_users_name.setText(rez_user_info[0]['USER_NAME'])
        self.ui._le_w_users_password.setText(rez_user_info[0]['USER_PASSWORD'])
        self.ui._le_w_users_mail.setText(rez_user_info[0]['USER_EMAIL'])
        self.ui._le_w_users_contract.setText(str(rez_user_info[0]['CONTRACT_NUMBER']))
        self.ui._le_w_users_cash.setText(str(rez_user_info[0]['USER_BALANCE']))
        self.ui._le_w_users_tariff.setText(rez_user_info[0]['TARIFF_NAME'])
        self.ui._le_w_users_pull.setText(rez_user_info[0]['PULL_NAME'])
        self.ui._le_w_users_ip.setText(rez_user_info[0]['USER_IP'])
        if (rez_user_info[0]['USER_STATUS'] == 1):
            self.ui._le_w_users_state.setText("Активен")
        else:
            self.ui._le_w_users_state.setText("Неактивен")
        cur.close()



# functions.user_get_ip()

#user_login = "ivan1"
# functions.change_user_ip(user_login)

# функция ввода двух типо операции
# functions.insert_operation_type()


#functions.insert_tariff(tariff_name, tariff_limit, tariff_description, tariff_price_per_month) #создать тариф

# создание ip пула
pull_name = "opt_turbo_51"
tariff_name = "Турбо"
pull_description = "Супер-ускоренное подключение"
#functions.create_ip_pull(pull_name, tariff_name, pull_description)

# внесение ip адресов в таблицу
#functions.create_ip_table()


# функция списания денег за день
#functions.pay_for_day()

# вывод всех пользователей
# functions.read_user()

# зачисление денег на счёт
# functions.refill_balance()


# Не юзабельны, но могут быть полезны потом
# Создание юзера
#log_user = "polina222"
#name_user = "polina"
#user_pass = "g45d"
#user_mail = "polina@mail.ru"
#user_status = 1
#contract_number = 777
#tariff_name = "Ускоренный"
#user_balance = 600
#functions.insert_user(log_user, name_user, user_pass, user_mail, user_status, contract_number, tariff_name, user_balance)

# Создание договора
#cntr_number = random.randint(1, 1000)
#first_name = "Николай"
#second_name = "Игольницын"
# functions.create_dogovor(cntr_number, first_name, second_name)

# functions.insert_into_user(user_pass, user_mail, login) #вставить юзеру

# functions.update_user(login, user_tariff_name)
# functions.delete_user(login) #удалить юзера по логину

# functions.delete_contract(contract_number)
# functions.search_user()
#######################################################

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Interface()
    window.show()
    sys.exit(app.exec_())
