import sys, json, os, re
sys.stdout.reconfigure(encoding='utf-8')
f = r'd:\tu_dong_giao_trinh\du_lieu\dau_ra\json\bf3899c3-6574-4eb7-bc0a-eeadf70a0e8c.json'
d = json.load(open(f, 'r', encoding='utf-8'))
refs = d.get('references', [])
print("Topic:", d.get("topic"))
print("Refs:", len(refs))
for r in refs[:3]:
    print("  id={} title={} url={}".format(r.get("id"), r.get("title"), r.get("url","")[:80]))
book = d.get('book_vi', {})
chs = book.get('chapters', [])
print("Chapters:", len(chs))
for ch in chs[:2]:
    secs = ch.get('sections', [])
    print("  {} -> {} sections".format(ch.get("title"), len(secs)))
    for sec in secs[:2]:
        content = sec.get('content','')
        ids_found = re.findall(r'\[(\d+)\]', content[:500])
        print("    {} | len={} | citations={}".format(sec.get("title"), len(content), ids_found[:5]))

# Check keys
print("\nAll keys:", list(d.keys()))
