import re
def section(path, head):
    s=open(path,encoding='utf-8').read()
    m=re.search(r'^## '+re.escape(head)+r'\n.*?(?=^## |^# )',s,re.M|re.S)
    return m.group(0)
DL=section('en/vol1.md','Downloading the Scripts')
VP=section('en/vol1.md','Volumes and Parts')
def build(a,b,vol,intro,out):
    parts=[]
    for n in range(a,b+1):
        s=open(f'en/vol{n}.md',encoding='utf-8').read()
        fm,body=re.match(r'^---\n(.*?)\n---\n(.*)$',s,re.S).groups()
        sub=re.search(r'^subtitle:\s*"(.*)"',fm,re.M).group(1)
        body=re.sub(r'## Downloading the Scripts\n.*?(?=\n## )','',body,count=1,flags=re.S)
        o=[];incode=False
        for l in body.split('\n'):
            if l.startswith('```'): incode=not incode
            if not incode:
                m=re.match(r'^(#{1,6}) (.*)$',l)
                if m: l='#'*min(len(m.group(1))+1,3)+' '+m.group(2)
            o.append(l)
        parts.append(f'# {sub}\n'+'\n'.join(o).strip('\n')+'\n')
    head=(f'---\ntitle: "AI Autonomous Cyber Defense System | Build Manual | {vol}"\n'
          f'subtitle: "Omnibus Edition: Parts {a}–{b}"\nauthor: "Isamu Tanaka"\nlang: en-US\n---\n\n'
          f'# About {vol}\n\n{intro}\n\n{DL}{VP}\n')
    open(out,'w',encoding='utf-8').write(head+'\n'.join(parts))
build(1,23,'Volume 1','''This book collects Volume 1 (Parts 1–23) of the "AI Autonomous Cyber Defense System Build Manual" in a single omnibus edition. It builds a defense foundation centered on Wazuh on Proxmox, then covers the Collector that saves alerts to PostgreSQL, integrated monitoring, the AI Defense Manager, a read-only Wazuh Indexer user, the relay API (Relay), AI analysis and its protection, and operational checks, arranging only the steps that succeeded, in chronological order, from the build records.

At the end of Volume 1 (Part 23), we found that the Wazuh Indexer audit log appeared not to be saved anywhere. This continues in Volume 2 (Part 24 onward).''','en/omnibus.md')
build(24,30,'Volume 2','''This book collects Volume 2 (Parts 24–30) of the "AI Autonomous Cyber Defense System Build Manual" in a single omnibus edition. On top of the environment built in Volume 1, it finds in the code why the Wazuh Indexer audit log was not being saved and makes it savable, then recovers the Collector that was found stopped during those checks without missing any events, and fixes it so that it does not stop for the same reason again.

It assumes the same environment as Volume 1 (Proxmox, VM 220 security-core, LXC 109 PostgreSQL and so on). For the underlying configuration and procedures, see Volume 1.''','en/omnibus_chu.md')
