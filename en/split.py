import re,json,sys
J=re.compile(r'[぀-ヿ一-鿿＀-￯]')
FENCE=re.compile(r'^```.*?\n.*?^```[ \t]*$',re.S|re.M)
allc={}
for n in range(1,31):
    s=open(f'vol{n}.md',encoding='utf-8').read()
    codes=[]
    def r(m):
        codes.append(m.group(0)); return f'⟦C{len(codes)-1}⟧'
    p=FENCE.sub(r,s)
    open(f'en/ja/vol{n}.prose.md','w',encoding='utf-8').write(p)
    json.dump(codes,open(f'en/ja/vol{n}.code.json','w',encoding='utf-8'),ensure_ascii=False)
    for c in codes:
        for l in c.split('\n')[1:-1]:
            if not J.search(l): continue
            m=re.match(r'^(\s*)(#|//|--|;)(.*)$',l)
            if m and not l.lstrip().startswith('#!'):
                allc[l]=''; continue
            m=re.match(r'^(.*?\S)(\s+#\s)(.*)$',l)
            if m and not J.search(m.group(1)): allc[l]=''
json.dump(allc,open('en/comments.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(allc))
