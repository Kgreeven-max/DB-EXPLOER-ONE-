"""
Check Mktg.TMP_RAWPRODUCTION_ETL table for historical ATM data.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Checking Mktg.TMP_RAWPRODUCTION_ETL")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Get column names
    print("COLUMNS IN Mktg.TMP_RAWPRODUCTION_ETL:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'Mktg' AND TABLE_NAME = 'TMP_RAWPRODUCTION_ETL'
            ORDER BY ORDINAL_POSITION
        """)
        cols = cursor.fetchall()
        for col in cols[:30]:
            print(f"  {col[0]} ({col[1]})")
        print(f"  ... (total {len(cols)} columns)")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check for date columns and PANEntryMode
    print("DATE AND PAN COLUMNS:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'Mktg' AND TABLE_NAME = 'TMP_RAWPRODUCTION_ETL'
              AND (COLUMN_NAME LIKE '%Date%' OR COLUMN_NAME LIKE '%PAN%' OR COLUMN_NAME LIKE '%Entry%')
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Get date range
    print("DATE RANGE:")
    print("-" * 60)
    try:
        # Try different date column names
        for date_col in ['LocalTransactionDate', 'TransactionDate', 'PostDate', 'Date']:
            try:
                cursor.execute(f"""
                    SELECT MIN([{date_col}]), MAX([{date_col}])
                    FROM Mktg.TMP_RAWPRODUCTION_ETL
                """)
                row = cursor.fetchone()
                print(f"  {date_col}: {row[0]} to {row[1]}")
                break
            except:
                continue
    except Exception as e:
        print(f"  Error getting dates: {e}")
    print()

    # Check PAN Entry Mode values
    print("PAN ENTRY MODE VALUES:")
    print("-" * 60)
    try:
        for pan_col in ['PANEntryMode', 'PAN Entry Mode', 'PanEntryMode']:
            try:
                cursor.execute(f"""
                    SELECT [{pan_col}], COUNT(*) as cnt
                    FROM Mktg.TMP_RAWPRODUCTION_ETL
                    GROUP BY [{pan_col}]
                    ORDER BY cnt DESC
                """)
                for row in cursor.fetchall()[:10]:
                    print(f"  '{row[0]}': {row[1]:,}")
                break
            except:
                continue
    except Exception as e:
        print(f"  Error getting PAN modes: {e}")
    print()

    # Sample data
    print("SAMPLE DATA (first 3 rows):")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 3 * FROM Mktg.TMP_RAWPRODUCTION_ETL")
        columns = [desc[0] for desc in cursor.description]
        print(f"Columns: {', '.join(columns[:10])}...")
        for row in cursor.fetchall():
            print(f"  {row[:5]}...")
    except Exception as e:
        print(f"  Error: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
