#!/bin/bash
# usage: en/pack_en.sh DIR
cd /home/claude && D=$1 && rm -rf $D && mkdir $D && cd $D && P="AI-Cyber-Defense-Build-Manual"
for n in $(seq 1 71); do v=Volume1; [ $n -ge 24 ] && v=Volume2; [ $n -ge 31 ] && v=Volume3; [ $n -ge 45 ] && v=Volume4; nn=$(printf %02d $n)
 cp ../en/out/vol${n}_A4.docx "${P}_${v}_Part${nn}_Word_A4.docx"
 cp ../en/out/vol${n}_KDP_6x9.docx "${P}_${v}_Part${nn}_KDP_Paperback_6x9.docx"
 cp ../en/out/vol${n}_Kindle.epub "${P}_${v}_Part${nn}_Kindle.epub"; done
for t in "omnibus Volume1 Parts01-23" "omnibus_chu Volume2 Parts24-30" "omnibus_ko Volume3 Parts31-44" "omnibus_zoku Volume4 Parts45-71"; do set -- $t
 cp ../en/out/$1_A4.docx "${P}_$2_Omnibus_$3_Word_A4.docx"; cp ../en/out/$1_KDP_6x9.docx "${P}_$2_Omnibus_$3_KDP_Paperback_6x9.docx"; cp ../en/out/$1_Kindle.epub "${P}_$2_Omnibus_$3_Kindle.epub"; done
zip -q "${P}_English_All_Outputs_Parts01-71.zip" *.docx *.epub
cd .. && zip -q $D/英語版_作業一式_原稿と変換スクリプト.zip en/*.md en/*.py en/*.sh en/comments.json en/tr/*.md en/ja/* build.sh build_docx.js fix_toc.py epub.css
