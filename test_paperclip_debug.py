#!/usr/bin/env python3
"""详细测试 paperclip 集成 - 查看原始输出"""

import subprocess
import sys

print("=" * 70)
print("直接在 WSL 中运行 paperclip 命令")
print("=" * 70)

# Test 1: 检查 paperclip 版本
print("\n[1] 检查 paperclip 版本:")
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "bash", "-c", "~/.local/bin/paperclip --version"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
print(f"stdout: {result.stdout}")
if result.stderr:
    print(f"stderr: {result.stderr}")
print(f"return code: {result.returncode}")

# Test 2: 尝试搜索 (可能需要登录)
print("\n[2] 搜索 'PROTAC':")
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "bash", "-c", '~/.local/bin/paperclip search "PROTAC"'],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=15,
)
print(f"stdout ({len(result.stdout)} chars): {result.stdout[:500]}")
if result.stderr:
    print(f"stderr ({len(result.stderr)} chars): {result.stderr[:500]}")
print(f"return code: {result.returncode}")

# Test 3: 检查是否需要登录
print("\n[3] 检查 paperclip 配置状态:")
result = subprocess.run(
    ["wsl", "-d", "Ubuntu", "bash", "-c", "~/.local/bin/paperclip config"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=15,
)
print(f"stdout: {result.stdout[:1000]}")
if result.stderr:
    print(f"stderr: {result.stderr[:500]}")
print(f"return code: {result.returncode}")

print("\n" + "=" * 70)
print("分析:")
print("- 如果看到 'paperclip not found'，说明路径有问题")
print("- 如果看到 'Authentication required' 或 'Login'，需要在 WSL 中先运行: paperclip login")
print("- 如果看到查询结果，则集成完全成功!")
print("=" * 70)
