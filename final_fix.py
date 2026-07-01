import sys
import os

def fix_all():
    # Fix store.py
    path = "sakthai/memory/store.py"
    with open(path, "r") as f:
        lines = f.readlines()

    # 1. Remove duplicate add_facts and fix stats mypy
    # Also fix import_from_dict logic

    new_lines = []
    skip_until_next_def = False
    in_import_from_dict = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Mypy fixes in stats()
        if 'r["tag"]: r["n"]' in line:
            line = line.replace('r["n"]', 'int(r["n"])')
        if '"tags": dict(sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))),' in line:
            line = line.replace('kv[1]', 'int(kv[1])')

        # Detect start of import_from_dict to fix its logic
        if "def import_from_dict(" in line:
            in_import_from_dict = True
            new_lines.append(line)
            # Skip until we find the try: block
            i += 1
            while i < len(lines) and "try:" not in lines[i]:
                new_lines.append(lines[i])
                i += 1
            if i < len(lines):
                new_lines.append(lines[i]) # try:
                i += 1
                # Skip the messed up logic inside try
                while i < len(lines) and "return (len(facts), len(obs))" not in lines[i]:
                    i += 1

                # Insert the correct logic
                new_lines.append("            self._conn.execute(\"BEGIN IMMEDIATE\")\n")
                new_lines.append("            if mode == \"replace\":\n")
                new_lines.append("                self._conn.execute(\"DELETE FROM facts\")\n")
                new_lines.append("                self._conn.execute(\"DELETE FROM observations\")\n")
                new_lines.append("                with contextlib.suppress(sqlite3.OperationalError):\n")
                new_lines.append("                    self._conn.execute(\n")
                new_lines.append("                        \"DELETE FROM sqlite_sequence WHERE name IN ('facts', 'observations')\"\n")
                new_lines.append("                    )\n")
                new_lines.append("\n")
                new_lines.append("            f_cols = [\"kind\", \"key\", \"value\", \"source_session\", \"created_at\", \"updated_at\", \"tags\"]\n")
                new_lines.append("            if mode == \"replace\":\n")
                new_lines.append("                f_cols.insert(0, \"id\")\n")
                new_lines.append("            f_qs = \", \".join([\"?\"] * len(f_cols))\n")
                new_lines.append("            f_stmt = \"INSERT INTO facts (\" + \", \".join(f_cols) + \") VALUES (\" + f_qs + \")\"  # nosec B608\n")
                new_lines.append("            f_rows: list[tuple[Any, ...]] = []\n")
                new_lines.append("            for f in facts:\n")
                new_lines.append("                r = [f[\"kind\"], f[\"key\"], f[\"value\"], f[\"source_session\"], f.get(\"created_at\", 0), f.get(\"updated_at\", 0), _encode_tags(f.get(\"tags\"))]\n")
                new_lines.append("                if mode == \"replace\": r.insert(0, f[\"id\"])\n")
                new_lines.append("                f_rows.append(tuple(r))\n")
                new_lines.append("            self._conn.executemany(f_stmt, f_rows)\n")
                new_lines.append("\n")
                new_lines.append("            o_cols = [\"summary\", \"evidence_session_id\", \"weight\", \"confidence\", \"created_at\"]\n")
                new_lines.append("            if mode == \"replace\":\n")
                new_lines.append("                o_cols.insert(0, \"id\")\n")
                new_lines.append("            o_qs = \", \".join([\"?\"] * len(o_cols))\n")
                new_lines.append("            o_stmt = \"INSERT INTO observations (\" + \", \".join(o_cols) + \") VALUES (\" + o_qs + \")\"  # nosec B608\n")
                new_lines.append("            o_rows: list[tuple[Any, ...]] = []\n")
                new_lines.append("            for o in obs:\n")
                new_lines.append("                r = [o[\"summary\"], o[\"evidence_session_id\"], o[\"weight\"], o[\"confidence\"], o[\"created_at\"]]\n")
                new_lines.append("                if mode == \"replace\": r.insert(0, o[\"id\"])\n")
                new_lines.append("                o_rows.append(tuple(r))\n")
                new_lines.append("            self._conn.executemany(o_stmt, o_rows)\n")
                new_lines.append("            self._conn.commit()\n")
                new_lines.append("        except Exception:\n")
                new_lines.append("            self._conn.rollback()\n")
                new_lines.append("            raise\n")

                # Now we are at return (len(facts), len(obs))
                new_lines.append(lines[i])
                in_import_from_dict = False
                i += 1
                continue

        # Detect the second (duplicate) add_facts and skip it
        if "def add_facts(self, facts: Iterable[dict[str, Any]]) -> list[int]:" in line:
            # Check if we already have one
            already_have_it = any("def add_facts" in l for l in new_lines)
            if already_have_it:
                # Skip this one
                i += 1
                while i < len(lines) and not (lines[i].startswith("    def ") or lines[i].startswith("def ")):
                    i += 1
                continue

        new_lines.append(line)
        i += 1

    with open(path, "w") as f:
        f.writelines(new_lines)

    # Fix openai_provider.py
    path_openai = "sakthai/agent/providers/openai_provider.py"
    with open(path_openai, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if 'return lambda: _stream_chat(client, payload, on_token)' in line:
             new_lines.append('        callback = on_token\n')
             new_lines.append('        return lambda: _stream_chat(client, payload, callback)\n')
        elif 'callback = on_token' in line:
             continue # skip duplicate if any
        else:
             new_lines.append(line)

    with open(path_openai, "w") as f:
        f.writelines(new_lines)

fix_all()
