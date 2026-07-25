import urllib.request, re

units = {
    0: [1],
    1: list(range(1, 12)),
    2: list(range(1, 10)),
    3: list(range(1, 8)),
    4: list(range(1, 7)),
    5: list(range(1, 9)),
    6: list(range(1, 11)),
    7: list(range(1, 10)),
}

for ch, unit_list in units.items():
    if not unit_list:
        continue
    # Get first unit for chapter title
    url = f'https://huggingface.co/learn/llm-course/chapter{ch}/{unit_list[0]}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8')
        
        # Get main content area - look for article or main text
        if 'article' in content:
            body = content.split('article')[1][:500] if 'article' in content.split('article')[1:] else ''
        else:
            body = content[:2000]
        
        # Get h1/h2 and paragraph text
        texts = re.findall(r'<(?:h[12]|p)[^>]*>(.*?)</(?:h[12]|p)>', content[:3000])
        clean = [re.sub(r'<[^>]+>', '', t).strip() for t in texts if re.sub(r'<[^>]+>', '', t).strip()]
        
        # Get page title
        pagetitle = ''
        title_match = re.search(r'<title>(.*?)</title>', content)
        if title_match:
            pagetitle = title_match.group(1)
        
        print(f'=== Chapter {ch} / Unit {unit_list[0]} ===')
        print(f'Page title: {pagetitle}')
        for c in clean[:8]:
            print(f'  {c[:120]}')
        print()
        
        # Get unit titles from sidebar/nav 
        unit_titles = re.findall(r'<a[^>]*href="[^"]*chapter' + str(ch) + r'/(\d+)"[^>]*>([^<]+)</a>', content)
        seen = set()
        for u, t in unit_titles:
            if u not in seen:
                print(f'  Unit {u}: {t.strip()[:80]}')
                seen.add(u)
        print()
    except Exception as e:
        print(f'Chapter {ch}: Error - {e}')
        print()
