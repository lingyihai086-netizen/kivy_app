# -*- coding: utf-8 -*-
import os
import json
import re

RULES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "link_rules.json")

DEFAULT_DOMAINS = ["kitty-kats.net", "adultphotosets.best", "image.imx.to"]
DEFAULT_SUFFIXES = ["cover.jpg", "cover-clean.jpg"]
DEFAULT_REPLACE_RULES = [
    (r't.imx.to/t/', 'i.imx.to/i/'),
    (r'(https?://)t(\d+\.pixhost\.to)/thumbs/', r'\1img\2/images/'),
]
DEFAULT_FILENAME_OLD = "Zazie"
DEFAULT_FILENAME_NEW = "aleksandrina"

class LinkRules:
    def __init__(self):
        self.domains = DEFAULT_DOMAINS.copy()
        self.suffixes = DEFAULT_SUFFIXES.copy()
        self.replace_rules = DEFAULT_REPLACE_RULES.copy()
        self.filename_old = DEFAULT_FILENAME_OLD
        self.filename_new = DEFAULT_FILENAME_NEW
        self.load()

    def load(self):
        if os.path.exists(RULES_FILE):
            try:
                with open(RULES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.domains = data.get('domains', self.domains)
                self.suffixes = data.get('suffixes', self.suffixes)
                self.replace_rules = data.get('replace_rules', self.replace_rules)
                self.filename_old = data.get('filename_old', self.filename_old)
                self.filename_new = data.get('filename_new', self.filename_new)
            except:
                pass

    def save(self):
        data = {
            'domains': self.domains,
            'suffixes': self.suffixes,
            'replace_rules': self.replace_rules,
            'filename_old': self.filename_old,
            'filename_new': self.filename_new
        }
        try:
            with open(RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

def process_links_lines(lines):
    rules = LinkRules()
    lines = [l.strip() for l in lines if l.strip()]
    if not lines:
        return [], {'deleted':0, 'replace_rules':[0]*len(rules.replace_rules), 'pixhost_rule':0, 'old_rule':0, 'original_count':0}
    new_lines, counter = [], 1
    stats = {'deleted':0, 'replace_rules':[0]*len(rules.replace_rules), 'pixhost_rule':0, 'old_rule':0, 'original_count':len(lines)}
    for line in lines:
        orig = line
        if any(d in orig for d in rules.domains) or any(orig.endswith(s) for s in rules.suffixes):
            stats['deleted'] += 1
            continue
        cur = orig
        for i, (pat, repl) in enumerate(rules.replace_rules):
            cur, cnt = re.subn(pat, repl, cur, flags=re.IGNORECASE)
            stats['replace_rules'][i] += cnt
        if 'pixhost.to' in cur and '/images/' in cur:
            cur = cur.replace(rules.filename_old, rules.filename_new)
            stats['pixhost_rule'] += 1
        if '/th/' in cur and '.jpg' in cur:
            mod = cur.replace('/th/', '/i/', 1)
            idx = mod.rfind('.jpg')
            if idx != -1:
                mod = mod[:idx+4] + f"/img__{counter:03d}.jpg" + mod[idx+4:]
                cur = mod
                stats['old_rule'] += 1
                counter += 1
        new_lines.append(cur)
    stats['total_modified'] = stats['old_rule'] + stats['pixhost_rule'] + sum(stats['replace_rules'])
    return new_lines, stats