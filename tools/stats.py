# -*- coding: utf-8 -*-
# 体检脚本：统计各课的密度（汉字/学时）、配图数、结构块数
# 用法：python tools/stats.py
import os, re, io

rows = []
for n in sorted(os.listdir('content')):
    if not n.endswith('.md') or n.startswith('_'):
        continue
    s = io.open('content/' + n, encoding='utf-8').read()
    m = re.search(r'^hours:\s*([\d.]+)', s, re.M)
    h = float(m.group(1)) if m else 0.0
    cn = len(re.findall(r'[\u4e00-\u9fa5]', s))
    figs = len(re.findall(r'^:::fig', s, re.M))
    goal = len(re.findall(r'^:::goal', s, re.M))
    quiz = len(re.findall(r'^:::quiz', s, re.M))
    term = len(re.findall(r'^:::term', s, re.M))
    rows.append((cn / max(h, 0.1), cn, h, figs, goal, quiz, term, n[:-3]))

rows.sort()
head = '%7s %8s %5s %3s %4s %4s %4s  课'
print(head % ('字/学时', '汉字', '学时', '图', 'goal', 'quiz', 'term'))
for d, cn, h, f, g, q, t, i in rows:
    flag = ' <<<' if (g == 0 or q == 0 or (h >= 2 and f == 0)) else ''
    print('%7.0f %8d %5.1f %3d %4d %4d %4d  %s%s' % (d, cn, h, f, g, q, t, i, flag))
print('总汉字', sum(r[1] for r in rows), '课程数', len(rows),
      '缺图课数', sum(1 for r in rows if r[2] >= 2 and r[3] == 0))
