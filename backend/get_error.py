import sqlite3
import traceback

try:
    conn = sqlite3.connect('searchx.db')
    cur = conn.cursor()
    cur.execute("SELECT processing_error FROM media_files WHERE original_filename='10.pdf'")
    res = cur.fetchone()
    print("Database error:", repr(res[0]) if res else 'None')
    conn.close()
except Exception as e:
    traceback.print_exc()
