#!/usr/bin/env python3
from pathlib import Path

p = Path('/das/user/QYJI/druggability/OXTR_assessment/presentations/generate_html_deck.py')
content = p.read_text()

replacements = [
    ('height: 48px;\n      background: #001965;', 'height: 52px;\n      background: #001965;'),
    ('font-size: 11.5px;\n      padding: 3px 8px;\n      border-radius: 4px;', 'font-size: 13px;\n      padding: 3px 9px;\n      border-radius: 4px;'),
    ('font-size: 14px;\n      font-weight: 600;\n      color: #E2E8F0;', 'font-size: 15px;\n      font-weight: 700;\n      color: #E2E8F0;'),
    ('font-size: 11px;\n      font-weight: 700;\n      padding: 2px 6px;', 'font-size: 12px;\n      font-weight: 700;\n      padding: 2px 7px;'),
    ('padding: 3px 12px;\n      border-radius: 20px;', 'padding: 4px 14px;\n      border-radius: 20px;'),
    ('font-size: 14.5px;\n      font-weight: 700;\n      color: #38BDF8;', 'font-size: 15.5px;\n      font-weight: 800;\n      color: #38BDF8;'),
    ('font-size: 12px;\n      color: #CBD5E1;\n      border-left: 1px solid rgba(255,255,255,0.2);', 'font-size: 13.5px;\n      color: #CBD5E1;\n      border-left: 1px solid rgba(255,255,255,0.2);'),
    ('font-size: 10.5px;\n      font-weight: 700;\n      padding: 2px 8px;', 'font-size: 11.5px;\n      font-weight: 800;\n      padding: 2px 9px;'),
    ('padding: 5px 12px;\n      border-radius: 6px;\n      font-size: 12px;', 'padding: 6px 14px;\n      border-radius: 6px;\n      font-size: 13px;'),
    ('padding: 38px 48px 30px 48px;', 'padding: 26px 44px 20px 44px;'),
    ('margin-bottom: 12px;\n      flex-shrink: 0;\n    }\n    .category-badge {\n      display: inline-block;\n      font-size: 11px;', 'margin-bottom: 8px;\n      flex-shrink: 0;\n    }\n    .category-badge {\n      display: inline-block;\n      font-size: 13px;'),
    ('font-size: 26px;\n      font-weight: 700;', 'font-size: 30px;\n      font-weight: 800;'),
    ('font-size: 14px;\n      color: var(--text-muted);\n      line-height: 1.4;', 'font-size: 16.5px;\n      color: var(--text-muted);\n      line-height: 1.45;'),
    ('padding: 16px 18px;\n      box-shadow: var(--shadow-sm);\n      font-size: 14px;', 'padding: 16px 20px;\n      box-shadow: var(--shadow-sm);\n      font-size: 15.5px;'),
    ('font-size: 14.5px;\n      font-weight: 700;\n      color: var(--nn-blue);\n      margin-bottom: 10px;', 'font-size: 17.5px;\n      font-weight: 800;\n      color: var(--nn-blue);\n      margin-bottom: 10px;'),
    ('padding-left: 14px;\n      margin-bottom: 8px;\n      font-size: 13.5px;\n      line-height: 1.45;', 'padding-left: 16px;\n      margin-bottom: 9px;\n      font-size: 15.5px;\n      line-height: 1.5;'),
    ('font-size: 12.5px;\n      color: #64748B;\n      margin-top: 3px;\n      margin-left: 4px;\n      line-height: 1.35;', 'font-size: 14.5px;\n      color: #475569;\n      margin-top: 4px;\n      margin-left: 4px;\n      line-height: 1.45;'),
    ('padding: 2px 7px;\n      border-radius: 4px;\n      font-size: 11px;', 'padding: 3px 8px;\n      border-radius: 4px;\n      font-size: 12.5px;'),
    ('padding: 10px 14px;\n      border-radius: 6px;\n      font-size: 13px;', 'padding: 12px 16px;\n      border-radius: 6px;\n      font-size: 15px;'),
    ('font-size: 11px;\n      color: #64748B;\n      text-align: center;\n      margin-top: 6px;\n      line-height: 1.3;', 'font-size: 13.5px;\n      color: #475569;\n      text-align: center;\n      margin-top: 8px;\n      line-height: 1.4;\n      font-weight: 500;'),
    ('font-size: 12px;\n      margin-top: 6px;\n    }\n    .styled-table th {\n      background: var(--nn-blue);\n      color: #FFFFFF;\n      padding: 6px 10px;', 'font-size: 13.5px;\n      margin-top: 6px;\n    }\n    .styled-table th {\n      background: var(--nn-blue);\n      color: #FFFFFF;\n      padding: 8px 12px;'),
    ('padding: 5px 10px;\n      border-bottom: 1px solid var(--border-subtle);', 'padding: 7px 12px;\n      border-bottom: 1px solid var(--border-subtle);'),
    ('padding: 8px 12px;\n      font-size: 12.5px;\n    }\n    .evidence-node strong {\n      color: var(--nn-blue);\n      font-size: 12.5px;', 'padding: 10px 14px;\n      font-size: 14.5px;\n    }\n    .evidence-node strong {\n      color: var(--nn-blue);\n      font-size: 15px;'),
    ('.node-tag { float: right; font-size: 10.5px;', '.node-tag { float: right; font-size: 12.5px;'),
    ('font-size: 11.5px;\n      color: #94A3B8;\n      flex-shrink: 0;', 'font-size: 13px;\n      color: #64748B;\n      flex-shrink: 0;'),
    ('height: 44px;\n      background: #001965;', 'height: 48px;\n      background: #001965;'),
    ('padding: 4px 10px;\n      border-radius: 4px;\n      font-size: 12px;\n      cursor: pointer;', 'padding: 5px 12px;\n      border-radius: 4px;\n      font-size: 13px;\n      cursor: pointer;'),
    ('font-size: 13px;\n      font-weight: 600;\n      color: #E2E8F0;', 'font-size: 14px;\n      font-weight: 700;\n      color: #E2E8F0;'),
    ('font-size: 11.5px;\n      color: #94A3B8;\n      display: flex;', 'font-size: 12.5px;\n      color: #CBD5E1;\n      display: flex;'),
    ('width: 460px;', 'width: 480px;'),
    ('font-size: 14px;\n      font-weight: 700;\n      color: #FFFFFF;', 'font-size: 15.5px;\n      font-weight: 700;\n      color: #FFFFFF;'),
    ('font-size: 13.5px;\n      line-height: 1.5;', 'font-size: 15px;\n      line-height: 1.6;'),
    ('font-size: 12.5px;\n      color: var(--nn-blue);\n      margin-bottom: 6px;', 'font-size: 13.5px;\n      color: var(--nn-blue);\n      margin-bottom: 8px;'),
    ('font-size: 20px;\n      font-weight: 700;\n      color: #38BDF8;', 'font-size: 22px;\n      font-weight: 800;\n      color: #38BDF8;'),
    ('.hud-title { font-size: 13px;', '.hud-title { font-size: 13.5px;'),
    ('.hud-stat { font-size: 22px;', '.hud-stat { font-size: 24px;'),
    ('<p style="line-height:1.65; color:#0F172A; font-size:13.5px;">${notes.spoken_script_zh}</p>', '<p style="line-height:1.68; color:#0F172A; font-size:15px;">${notes.spoken_script_zh}</p>'),
    ('<p style="font-size:12px; color:#64748B; line-height:1.5;">${notes.spoken_script_en}</p>', '<p style="font-size:13px; color:#64748B; line-height:1.55;">${notes.spoken_script_en}</p>')
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
    else:
        print(f"Warning: snippet not found: {repr(old[:30])}")

p.write_text(content)
print(f"Successfully applied {count}/{len(replacements)} typography enhancements to OXTR generate_html_deck.py!")
