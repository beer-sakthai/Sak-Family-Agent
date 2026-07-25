import urllib.request, re, sys

for ch in range(0, 8):
    url = f'https://huggingface.co/learn/llm-course/chapter{ch}/1'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8')
        
        title_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content)
        subtitle_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', content)
        
        title = re.sub(r'<[^>]+>', '', title_matches[0]).strip() if title_matches else 'No title'
        subtitles = [re.sub(r'<[^>]+>', '', s).strip() for s in subtitle_matches[:5] if re.sub(r'<[^>]+>', '', s).strip()]
        
        unit_links = re.findall(r'href="[^"]*chapter' + str(ch) + r'/(\d+)"', content)
        max_unit = max([int(u) for u in unit_links]) if unit_links else 0
        
        print(f'Chapter {ch}: {title}')
        print(f'  Units: 1-{max_unit}')
        for s in subtitles:
            print(f'  > {s}')
        print()
    except Exception as e:
        print(f'Chapter {ch}: Error - {e}')
        print()
