import os
import time
import shutil
from datetime import datetime

# Absolute path to your db.sqlite3 file
DB_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

# Absolute path to the backups directory
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Track last modified time
last_modified = None

print("📁 Watching for changes in db.sqlite3...")

while True:
    try:
        current_modified = os.path.getmtime(DB_PATH)
        if last_modified is None:
            last_modified = current_modified

        if current_modified != last_modified:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(BACKUP_DIR, f'db_backup_{timestamp}.sqlite3')
            shutil.copy2(DB_PATH, backup_file)
            print(f"✅ Backup created: {backup_file}")
            last_modified = current_modified

        time.sleep(10)  # Check every 10 seconds
    except KeyboardInterrupt:
        print("🛑 Stopped watching.")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(10)
