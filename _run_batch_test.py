"""临时测试 — 演示 batch 功能"""
import time
from litkit.druggability.batch import assess_druggability_batch

# 多类型靶点组合：已验证的 + 较难的 + 免疫靶点
targets = ["EGFR", "BRAF", "KRAS", "TP53", "PD1", "CTLA4"]
print(f"Testing {len(targets)} targets: {targets}")
start = time.time()

results = assess_druggability_batch(targets, show_progress=False, request_delay=0)

elapsed = time.time() - start
print(f"\nTook {elapsed:.1f}s total ({elapsed/len(targets):.1f}s avg per target)")

print(f"{'Target':20s} {'Overall':8s} {'Conf':10s} {'Tractab':8s} {'Ligand':8s} {'Error':40s}")
print("-"*94)
for r in results:
    tract = f"{r.tractability_score:.3f}" if r.tractability_score else "N/A"
    lig = f"{r.ligandability_score:.3f}" if r.ligandability_score else "N/A"
    err = (r.error[:40] if r.error else "") if not r.success else ""
    print(f"{r.query:20s} {r.overall_score:>8.3f} {r.confidence:>10s} {tract:>8s} {lig:>8s} {err:40s}")

print(f"\n{sum(1 for r in results if r.success)}/{len(results)} succeeded")