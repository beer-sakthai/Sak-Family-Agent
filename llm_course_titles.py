import urllib.request, re

units_to_fetch = {
    0: [1],
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    2: [1, 9],
    3: [1, 7],
    4: [1, 6],
    5: [1, 8],
    6: [1, 10],
    7: [1, 9],
}

for ch, unit_list in units_to_fetch.items():
    for unit in unit_list:
        url = f'https://huggingface.co/learn/llm-course/chapter{ch}/{unit}.md'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                content = r.read().decode('utf-8')
            
            lines = content.split('\n')
            # Get the first heading after the front matter
            title = ''
            first_para = ''
            for line in lines:
                if line.startswith('# ') and not line.startswith('# '):
                    title = line
                elif line.strip() and not line.startswith('{') and not line.startswith('---'):
                    first_para = line.strip()[:120]
                    break
            
            if not title:
                # Try to get from first heading
                for line in lines:
                    if line.startswith('# ') and 'Introduction' not in line:
                        title = line[:80]
                        break
                    elif line.startswith('# '):
                        title = line[:80]
                        break
            
            print(f'Ch{ch}/U{unit}: {title[:80] if title else "?"}')
            if first_para:
                print(f'  -> {first_para}')
            
        except Exception as e:
            print(f'Ch{ch}/U{unit}: Error - {e}')
    print()
