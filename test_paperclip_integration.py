#!/usr/bin/env python3
"""快速测试 paperclip 集成"""

import sys
import json

sys.path.insert(0, 'src')

from bbbkit.search import search_paperclip, search

print("=" * 60)
print("测试 1: 直接调用 search_paperclip()")
print("=" * 60)

try:
    results = search_paperclip("PROTAC druggability", limit=3)
    print(f"✓ 成功搜索 {len(results)} 篇论文")
    
    for i, paper in enumerate(results, 1):
        print(f"\n  论文 {i}:")
        print(f"    Title: {paper.get('title', 'N/A')[:80]}")
        print(f"    URL: {paper.get('url', 'N/A')}")
        print(f"    PMID: {paper.get('pmid', 'N/A')}")
        print(f"    Source: {paper.get('source', 'N/A')}")
    
except Exception as e:
    print(f"✗ 失败: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("测试 2: 使用统一接口 search()")
print("=" * 60)

try:
    results = search("protein design", source="paperclip", limit=3)
    print(f"✓ 成功搜索 {len(results)} 篇论文")
    
    for i, paper in enumerate(results, 1):
        print(f"\n  论文 {i}:")
        print(f"    Title: {paper.get('title', 'N/A')[:80]}")
        print(f"    PMID: {paper.get('pmid', 'N/A')}")
    
except Exception as e:
    print(f"✗ 失败: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
