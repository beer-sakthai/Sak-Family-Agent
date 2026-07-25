import urllib.request, re

# Fetch all units for all chapters
for ch in range(0, 8):
    # First get the chapter index to know how many units
    url = f'https://huggingface.co/learn/llm-course/chapter{ch}/1'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8')
        # Get all unit numbers
        unit_nums = re.findall(r'href="[^"]*chapter' + str(ch) + r'/(\d+)"', content)
        unit_nums = sorted(set(unit_nums))
    except:
        continue

    print(f'=== Chapter {ch} ===')
    
    for u in unit_nums:
        url2 = f'https://huggingface.co/learn/llm-course/chapter{ch}/{u}.md'
        req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req2, timeout=10) as r:
                md = r.read().decode('utf-8')
            
            # Find first # heading
            for line in md.split('\n'):
                if line.startswith('# ') and line.strip():
                    title = line[2:].strip()
                    # Remove anchor
                    title = re.sub(r'\[\[.*?\]\]', '', title).strip()
                    print(f'  Unit {u}: {title[:100]}')
                    break
            else:
                print(f'  Unit {u}: [no heading found]')
        except Exception as e:
            print(f'  Unit {u}: Error - {e}')
    
    print()
