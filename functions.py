from calendar import monthrange
from check_db import *
from datetime import datetime
import pymysql.connections
from params_win_base import *
from loguru import logger
from ipaddress import IPv4Network

try:
    con = pymysql.connect(
        host=hostname,
        port=3306,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("connect")
except Exception as ex:
    print("no connect")
    print(ex)

def check_tariff_exist(tariff_name):
    cur = con.cursor()
    sql_check_tariff = f"SELECT TARIFF_NAME FROM tariff " \
                       f"WHERE TARIFF_NAME = '{tariff_name}'"
    cur.execute(sql_check_tariff)
    result = cur.fetchone()
    if result is None:
        result_check = "No"
    else:
        result_check = result['TARIFF_NAME']
    cur.close()
    return str(result_check)


# внесение договора в базу
@logger.catch
def create_dogovor(cont_number, first_name, second_name, signal):
    cur = con.cursor()
    try:
        get_data_contract = datetime.now()
        contract_date = datetime.strftime(get_data_contract, '%Y-%m-%d %H:%M:%S')
        sql_create_dogovor = "INSERT INTO contract (CONTRACT_NUMBER," \
                             "FIRST_NAME, SECOND_NAME, CONTRACT_DATE) " \
                             "VALUES (%s, %s, %s, %s)"
        val = (cont_number, first_name, second_name, contract_date)
        cur.execute(sql_create_dogovor, val)
        signal.emit('Договор успешно внесён')
        con.commit()
        cur.close()
    except Exception as ex:
        signal.emit('Ошибка. Проверьте уникальность номера договора')
        print(ex)
        cur.close()


# внесение юзера в базу
@logger.catch
def insert_user(user_login, user_name, user_password, user_email, contract_number, tariff_name, user_balance, signal):
    cur = con.cursor()
    try:
        sql_get_ip = f"SELECT IP_ADDRESS FROM ip_table i " \
                     f"JOIN ip_pull p on i.IP_PULL = p.PULL_NAME " \
                     f"JOIN tariff t on p.TARIFF_NAME = t.TARIFF_NAME " \
                     f"JOIN users u on t.TARIFF_NAME = u.TARIFF_NAME " \
                     f"WHERE i.IP_STATUS = 0 " \
                     f"AND u.USER_LOGIN = '{user_login}'"

        sql_insert_user = "INSERT INTO users " \
                          "(USER_LOGIN, USER_NAME, USER_PASSWORD, USER_EMAIL, " \
                          "USER_STATUS, CONTRACT_NUMBER, TARIFF_NAME, USER_BALANCE) " \
                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (user_login, user_name, user_password, user_email, 1, contract_number, tariff_name, user_balance)
        cur.execute(sql_insert_user, val)
        cur.execute(sql_get_ip)
        rez_ip = cur.fetchone()
        ip = rez_ip['IP_ADDRESS']
        sql_ip_to_user = f"UPDATE users u " \
                         f"JOIN tariff t on u.TARIFF_NAME = t.TARIFF_NAME " \
                         f"JOIN ip_pull p on t.TARIFF_NAME = p.TARIFF_NAME " \
                         f"JOIN ip_table i on p.PULL_NAME = i.IP_PULL " \
                         f"SET u.USER_IP = i.IP_ADDRESS, " \
                         f"i.IP_STATUS = 1 " \
                         f"WHERE u.USER_LOGIN = '{user_login}' " \
                         f"AND i.IP_STATUS = 0 " \
                         f"AND i.IP_ADDRESS = '{ip}'"
        cur.execute(sql_ip_to_user)
        signal.emit('Пользователь успешно зарегистрирован')
        con.commit()
        cur.close()
    except Exception as ex:
        print(ex)
        signal.emit('Ошибка. Данный логин или номер контракта уже занят')
        con.rollback()
        cur.close()

def change_user_ip(user_login):
    cur = con.cursor()
    sql_get_ip = f"SELECT IP_ADDRESS FROM ip_table i " \
                 f"JOIN ip_pull p on i.IP_PULL = p.PULL_NAME " \
                 f"JOIN tariff t on p.TARIFF_NAME = t.TARIFF_NAME " \
                 f"JOIN users u on t.TARIFF_NAME = u.TARIFF_NAME " \
                 f"WHERE i.IP_STATUS = 0 " \
                 f"AND u.USER_LOGIN = '{user_login}'"
    cur.execute(sql_get_ip)
    rez_ip = cur.fetchone()
    print(rez_ip)
    ip = rez_ip['IP_ADDRESS']
    print(ip)
    sql_ip_to_user = f"UPDATE users u " \
                     f"JOIN tariff t on u.TARIFF_NAME = t.TARIFF_NAME " \
                     f"JOIN ip_pull p on t.TARIFF_NAME = p.TARIFF_NAME " \
                     f"JOIN ip_table i on p.PULL_NAME = i.IP_PULL " \
                     f"SET u.USER_IP = i.IP_ADDRESS, " \
                     f"i.IP_STATUS = 1 " \
                     f"WHERE u.USER_LOGIN = '{user_login}' " \
                     f"AND i.IP_STATUS = 0 " \
                     f"AND i.IP_ADDRESS = '{ip}'"
    cur.execute(sql_ip_to_user)
    con.commit()
    cur.close()


# внесение тарифа в базу
@logger.catch
def insert_tariff(tariff_name, tariff_limit, tariff_description, tariff_price_per_month):
    cur = con.cursor()
    sql_insert_tariff = "INSERT INTO tariff (TARIFF_NAME, TARIFF_LIMIT, " \
                        "TARIFF_DESCRIPTION, TARIFF_PRICE_PER_MONTH)" \
                        "VALUES (%s, %s, %s, %s)"
    val = (tariff_name, tariff_limit, tariff_description, tariff_price_per_month)
    cur.execute(sql_insert_tariff, val)
    con.commit()
    cur.close()


# внесение договора в базу
@logger.catch
def create_ip_pull(pull_name, tariff_name, pull_description):
    cur = con.cursor()
    sql_create_ip_pull = "INSERT INTO ip_pull (PULL_DESCRIPTION," \
                         "TARIFF_NAME, PULL_NAME)" \
                         " VALUES (%s, %s, %s)"
    val = (pull_description, tariff_name, pull_name)
    cur.execute(sql_create_ip_pull, val)
    con.commit()
    cur.close()


# заносим в таблицу ip адреса
def create_ip_table():
    cur = con.cursor()
    ip_status = 0
    pull_name = "opt_turbo_51"
    net = IPv4Network("192.168.5.0/24").hosts()
    for addr in net:
        sql_insert_ip = "INSERT INTO ip_table (IP_ADDRESS, IP_PULL, IP_STATUS) " \
                        "VALUES (%s, %s, %s)"
        val = (addr, pull_name, ip_status)
        cur.execute(sql_insert_ip, val)
    cur.close()
    con.commit()




# чтение юзера
@logger.catch
def read_user():
    with con.cursor() as cur:
        sql_read_user = "SELECT * FROM users"
        cur.execute(sql_read_user)
        rez = cur.fetchall()
        for row in rez:
            print(row["USER_ID"], row["USER_LOGIN"], row["USER_NAME"], row["USER_PASSWORD"], row["USER_EMAIL"],
                  row["USER_IP"], row["USER_STATUS"], row["CONTRACT_NUMBER"], row["TARIFF_NAME"], row["USER_BALANCE"])
        cur.close()


# списание денег за день
@logger.catch
def pay_for_day():
    try:
        cur = con.cursor()
        get_data = datetime.now()
        current_year = datetime.now().year
        current_month = datetime.now().month
        days = monthrange(current_year, current_month)
        day = days[1]
        data_now = datetime.strftime(get_data, '%Y-%m-%d %H:%M:%S')
        sql_get_balance = f"SELECT USER_BALANCE, TARIFF_PRICE_PER_MONTH, USER_LOGIN " \
                          f"FROM users u " \
                          f"JOIN tariff t ON u.TARIFF_NAME = t.TARIFF_NAME"
        cur.execute(sql_get_balance)
        rez_balance = cur.fetchall()
        print("REZ------>", rez_balance)
        for i in rez_balance:
            if (i['USER_BALANCE'] >= i['TARIFF_PRICE_PER_MONTH']/day):
                user_login = i['USER_LOGIN']
                print("USER_lOG---->", user_login)
                sql_transaction_pay = f"UPDATE users u " \
                                      f"JOIN tariff t on u.TARIFF_NAME = t.TARIFF_NAME " \
                                      f"SET u.USER_BALANCE = (USER_BALANCE - TARIFF_PRICE_PER_MONTH/{day}), " \
                                      f"u.USER_STATUS = 1 " \
                                      f"WHERE u.USER_BALANCE >= t.TARIFF_PRICE_PER_MONTH/{day} " \
                                      f"AND u.USER_LOGIN = '{user_login}'"
                cur.execute(sql_transaction_pay)
                con.commit()
                sql_insert_story = f"INSERT INTO operations (OPERATION_SUM, OPERATION_DATA, OPERATION_TYPE, " \
                                   f"OPERATION_OSTATOK, USER_LOGIN) " \
                                   f"SELECT t.TARIFF_PRICE_PER_MONTH/{day}, '{data_now}', 'Списание', u.USER_BALANCE, " \
                                   f"u.USER_LOGIN " \
                                   f"FROM users u " \
                                   f"JOIN tariff t " \
                                   f"ON u.TARIFF_NAME = t.TARIFF_NAME " \
                                   f"WHERE u.USER_LOGIN = '{user_login}'"
                cur.execute(sql_insert_story)
                con.commit()
            else:
                cur = con.cursor()
                sql_set_min_mark = f"UPDATE users u " \
                                   f"JOIN tariff t on u.TARIFF_NAME = t.TARIFF_NAME " \
                                   f"SET u.USER_STATUS = 0 " \
                                   f"WHERE u.USER_BALANCE < t.TARIFF_PRICE_PER_MONTH/{day}"
                cur.execute(sql_set_min_mark)
                con.commit()
        cur.close()
    except Exception as ex:
        print(ex)
        con.rollback()


# Пополнение баланса
def refill_balance():
    try:
        cur = con.cursor()
        print("Введите номер договора: ")
        contract_number = input()
        print("Введите сумму деняк: ")
        summa = input()
        get_data = datetime.now()
        data_now = datetime.strftime(get_data, '%Y-%m-%d %H:%M:%S')
        sql_transaction_refill = f"UPDATE users u SET u.USER_BALANCE = (u.USER_BALANCE + '{summa}'), " \
                                 f"u.USER_STATUS = 1 " \
                                 f"WHERE u.CONTRACT_NUMBER = '{contract_number}' "
        cur.execute(sql_transaction_refill)
        con.commit()
        sql_insert_story = f"INSERT INTO operations (OPERATION_SUM, OPERATION_DATA, OPERATION_TYPE, " \
                           f"OPERATION_OSTATOK, USER_LOGIN) " \
                           f"SELECT '{summa}', '{data_now}', 'Зачисление', u.USER_BALANCE, " \
                           f"u.USER_LOGIN " \
                           f"FROM users u " \
                           f"WHERE u.CONTRACT_NUMBER = {contract_number} "
        cur.execute(sql_insert_story)
        con.commit()
        cur.close()
    except Exception as ex:
        print(ex)
        con.rollback()


################################Не юзаемые функции сейчас

# удаление данных по полю
def delete_user(user_login):
    cur = con.cursor()
    sql_delete_data_login = f"DELETE FROM users WHERE USER_LOGIN = '{user_login}'"
    cur.execute(sql_delete_data_login)
    con.commit()
    cur.close()


def delete_contract(contract_number):
    cur = con.cursor()
    sql_delete_data_contract = f"DELETE FROM contract WHERE CONTRACT_NUMBER = '{contract_number}'"
    cur.execute(sql_delete_data_contract)
    con.commit()
    cur.close()


# вставка значений в существующего юзера
@logger.catch
def insert_into_user(user_password, user_email, user_login):
    cur = con.cursor()
    sql_insert_into_user = f"UPDATE users SET USER_PASSWORD = '{user_password}', USER_EMAIL = '{user_email}' " \
                           f"WHERE USER_LOGIN='{user_login}'"
    cur.execute(sql_insert_into_user)
    con.commit()
    cur.close()


@logger.catch
def update_user(user_login, user_tariff_name):
    cur = con.cursor()
    sql_insert_into_user = f"UPDATE users SET TARIFF_NAME = '{user_tariff_name}' " \
                           f"WHERE USER_LOGIN='{user_login}'"
    cur.execute(sql_insert_into_user)
    con.commit()
    cur.close()


def insert_operation_type():
    cur = con.cursor()
    sql_insert_optype = "INSERT INTO operation_type (OPERATION_TYPE_NAME) VALUES (%s)"
    op_type = "Списание"
    cur.execute(sql_insert_optype, op_type)
    op_type = "Зачисление"
    cur.execute(sql_insert_optype, op_type)
    con.commit()
    cur.close()
