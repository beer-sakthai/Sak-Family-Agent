import json
d = json.load(open('/tmp/spaces.json'))
print(f"Spaces count: {len(d)}")
print(f"Keys in first: {list(d[0].keys())}")
for item in d:
    sid = item.get('_id') or item.get('id') or item.get('spaceId', 'MISSING')
    if 'id' in item and 'spaceId' not in item:
        sid = item['id']
    print(f"  id={sid}  sdk={item.get('sdk','N/A')}  dl={item.get('downloads',0)}")
