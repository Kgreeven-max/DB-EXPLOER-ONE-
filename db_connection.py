#!/usr/bin/env python3
"""
Database Connection Module
Reusable MySQL connection for dbxdb
"""

import pymysql

# MySQL configuration
mysql_config = {
    'host': 'infinity-9ix.calcoastcu.org',
    'port': 3306,
    'user': 'Kendall.Greeven',
    'password': "Note9Shucran32!JelloAzulXie",
    'database': 'dbxdb',
    'charset': 'utf8mb4',
    'connect_timeout': 30,
}

def get_connection():
    """Create and return a MySQL connection"""
    return pymysql.connect(**mysql_config)
