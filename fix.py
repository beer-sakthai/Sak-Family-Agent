import re

files = [
    "sakthai-chat-cli/sakthai/memory/store.py",
    "personas/shared/sakthai/memory/store.py",
    "personas/sakthai/sakthai/memory/store.py",
]

for file in files:
    with open(file, "r") as f:
        content = f.read()

    new_content = content.replace(
        'self._conn.execute("PRAGMA busy_timeout={:d}".format(int(DB_BUSY_TIMEOUT_MS)))',
        'self._conn.execute(f"PRAGMA busy_timeout={int(DB_BUSY_TIMEOUT_MS)}")'
    )

    with open(file, "w") as f:
        f.write(new_content)
