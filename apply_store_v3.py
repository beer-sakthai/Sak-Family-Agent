content = open("sakthai/memory/store.py").read()
search = '        res = {'
replace = '        res: dict[str, Any] = {'
with open("sakthai/memory/store.py", "w") as f:
    f.write(content.replace(search, replace))
