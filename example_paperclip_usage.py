#!/usr/bin/env python3
"""
Paperclip 集成完整示例
演示在 druggability 项目中使用 paperclip 进行文献搜索
"""

import sys
sys.path.insert(0, 'src')

from bbbkit.search import search, search_paperclip
import json

print("=" * 70)
print("🔬 Paperclip 集成示例")
print("=" * 70)

# 示例 1: 搜索 PROTAC 相关论文
print("\n[示例 1] 搜索 PROTAC 论文")
print("-" * 70)

try:
    results = search_paperclip("PROTAC", limit=5)
    print(f"✓ 找到 {len(results)} 篇论文\n")
    
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
        if paper['authors']:
            print(f"   作者: {paper['authors'][:60]}...")
        if paper['url']:
            print(f"   URL: {paper['url']}")
        if paper['paper_id']:
            print(f"   ID: {paper['paper_id']}")
        print()
        
except Exception as e:
    print(f"✗ 失败: {e}\n")

# 示例 2: 使用统一接口搜索不同的主题
print("\n[示例 2] 统一接口搜索（使用 search()）")
print("-" * 70)

try:
    results = search("protein design", source="paperclip", limit=3)
    print(f"✓ 使用统一接口找到 {len(results)} 篇论文\n")
    
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title'][:70]}")
        if paper.get('abstract'):
            abstract = paper['abstract']
            print(f"   摘要: {abstract[:100]}...")
        print()
        
except Exception as e:
    print(f"✗ 失败: {e}\n")

# 示例 3: 指定数据库搜索
print("\n[示例 3] 搜索 PubMed Central 论文")
print("-" * 70)

try:
    results = search_paperclip("druggability", source_db="pmc", limit=3)
    print(f"✓ 在 PMC 中找到 {len(results)} 篇论文\n")
    
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
        print(f"   来源: {paper['source']}")
        print(f"   发表日期: {paper['publication_date']}")
        print()
        
except Exception as e:
    print(f"✗ 失败: {e}\n")

# 示例 4: 结合多个搜索源
print("\n[示例 4] 比较不同数据源")
print("-" * 70)

sources_to_try = [
    ("openalex", "PROTAC"),
    ("paperclip", "PROTAC"),
]

for source, query in sources_to_try:
    try:
        results = search(query, source=source, limit=2)
        print(f"\n✓ {source.upper()}: 找到 {len(results)} 篇论文")
        for r in results:
            title = r.get('title', '').split('\n')[0][:60]
            print(f"  - {title}")
    except Exception as e:
        print(f"✗ {source.upper()}: {type(e).__name__}")

print("\n" + "=" * 70)
print("💡 提示:")
print("  - search_paperclip() 支持 source_db 参数，如 'pmc', 'abstracts', 'fda'")
print("  - 在 Windows 中自动通过 WSL 调用 paperclip")
print("  - 需要先在 WSL 中运行: paperclip login")
print("=" * 70)
