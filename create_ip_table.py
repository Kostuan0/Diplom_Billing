#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pymysql.connections
from params import *
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

def create_ip_table():
    cur = con.cursor()
    ip_status = 0
    pull_name = "opt_def_51"
    net = IPv4Network("192.168.1.0/24").hosts()
    for addr in net:
        sql_insert_ip = "INSERT INTO ip_table (IP_ADDRESS, IP_PULL, IP_STATUS) " \
                        "VALUES (%s, %s, %s)"
        val = (addr, pull_name, ip_status)
        cur.execute(sql_insert_ip, val)
    con.commit()
    cur.close()

create_ip_table()