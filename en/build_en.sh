#!/bin/bash
cd /home/claude
for f in $(seq 1 39 | sed "s/^/vol/") omnibus omnibus_chu omnibus_ko; do
  ./build.sh en/$f.md en/out/${f}_A4 a4 > en/out/logs_$f.a4 2>&1 || echo "FAIL $f a4"
  ./build.sh en/$f.md en/out/${f}_KDP_6x9 kdp > en/out/logs_$f.kdp 2>&1 || echo "FAIL $f kdp"
  sl=1; case $f in omnibus*) sl=2;; esac
  t=$(grep -m1 '^title:' en/$f.md | sed 's/^title: "//; s/"$//; s/ | Build Manual | / Build Manual — /')
  pandoc en/$f.md -o en/out/${f}_Kindle.epub --toc --toc-depth=2 --split-level=$sl --css epub.css -f markdown-smart --metadata title="$t" 2>/dev/null || echo "FAIL $f epub"
  echo "DONE $f $(date +%T)"
done
echo ALLDONE
