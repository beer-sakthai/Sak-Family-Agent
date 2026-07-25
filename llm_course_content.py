import urllib.request, re

# Fetch key units for detailed content
key_units = [(2, 2), (2, 3), (2, 4), (2, 8), (4, 1), (4, 2), (5, 4), (5, 6), (6, 2), (6, 8), (7, 2), (7, 6)]

for ch, u in key_units:
    url = f'https://huggingface.co/learn/llm-course/chapter{ch}/{u}.md'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            md = r.read().decode('utf-8')
        
        # Get first 3 paragraphs after the title
        lines = md.split('\n')
        content_lines = []
        in_content = False
        p_count = 0
        for line in lines:
            if line.startswith('## ') and p_count < 3:
                content_lines.append(line[:120])
                p_count += 1
            elif line.startswith('```') and p_count < 3:
                content_lines.append(line[:80])
                p_count += 1
        
        # Get all ## headings to understand structure
        headings = [line.strip() for line in lines if line.startswith('## ')][:10]
        
        print(f'=== Ch{ch}/U{u} ===')
        print(f'Headings:')
        for h in headings:
            h2 = re.sub(r'\[\[.*?\]\]', '', h).strip()
            print(f'  {h2[:100]}')
        print()
    except Exception as e:
        print(f'Ch{ch}/U{u}: Error - {e}')
        print()
