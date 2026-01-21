"""
DWHA SQL Server Connection Module
Connects to the symwarehouse database on DWHA server for digital wallet queries.
"""
import pyodbc


def get_dwha_connection():
    """
    Establish connection to DWHA SQL Server using Windows Authentication.

    Returns:
        pyodbc.Connection: Active database connection

    Usage:
        conn = get_dwha_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ...")
        cursor.close()
        conn.close()
    """
    connection_string = (
        'Driver={ODBC Driver 17 for SQL Server};'
        'Server=DWHA;'
        'Database=symwarehouse;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(connection_string)


def test_connection():
    """Test the DWHA connection and print server info."""
    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print("Successfully connected to DWHA!")
        print(f"Server version: {version[:80]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
