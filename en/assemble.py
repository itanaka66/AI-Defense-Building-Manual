import re,json,sys
J=re.compile(r'[぀-ヿ一-鿿＀-￯]')
tr=json.load(open('en/comments.json',encoding='utf-8'))
INL=re.compile(r'`[^`\n]+`')
def run(n):
    codes=json.load(open(f'en/ja/vol{n}.code.json',encoding='utf-8'))
    ja=open(f'en/ja/vol{n}.prose.md',encoding='utf-8').read()
    en=open(f'en/tr/vol{n}.prose.md',encoding='utf-8').read()
    ph_ja=re.findall(r'⟦C\d+⟧',ja); ph_en=re.findall(r'⟦C\d+⟧',en)
    err=[]
    if ph_ja!=ph_en: err.append(f'placeholders differ: {len(ph_ja)} vs {len(ph_en)}; missing {sorted(set(ph_ja)-set(ph_en))} extra {sorted(set(ph_en)-set(ph_ja))}')
    a=sorted(x for x in INL.findall(ja) if not J.search(x)); b=sorted(x for x in INL.findall(en) if not J.search(x))
    from collections import Counter
    ca,cb=Counter(a),Counter(b)
    if ca-cb: err.append(f'inline code lost: {list((ca-cb).elements())[:10]}')
    jl=[l for l in en.split('\n') if J.search(re.sub(r'`[^`]*`','',l))]
    if jl: err.append(f'Japanese left in prose: {len(jl)} lines e.g. {jl[:3]}')
    def sub(m):
        c=codes[int(m.group(0)[2:-1])]
        return '\n'.join(tr.get(l,l) for l in c.split('\n'))
    out=re.sub(r'⟦C\d+⟧',sub,en)
    open(f'en/vol{n}.md','w',encoding='utf-8').write(out)
    return err
for n in map(int,sys.argv[1:]):
    e=run(n); print(n,'OK' if not e else e)
