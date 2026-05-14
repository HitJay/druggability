#!/usr/bin/env python3
"""
测试脚本：验证 ChEMBL 本地数据库模块的基本功能

这个测试不需要实际的 ChEMBL 数据库，主要验证代码逻辑和导入。
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """测试所有必要的导入"""
    print("=" * 60)
    print("测试 1: 导入测试")
    print("=" * 60)
    
    try:
        # 测试主模块导入
        from litkit.druggability import assess_ligandability
        print("✓ 成功导入 assess_ligandability")
        
        # 测试本地数据库模块导入
        from litkit.druggability import chembl_local
        print("✓ 成功导入 chembl_local 模块")
        
        # 测试类导入
        from litkit.druggability.chembl_local import ChemblLocalDB
        print("✓ 成功导入 ChemblLocalDB 类")
        
        # 测试便捷函数导入
        from litkit.druggability.chembl_local import (
            get_db,
            search_target,
            count_ligands,
            get_strongest_activity,
            count_approved_drugs
        )
        print("✓ 成功导入便捷函数")
        
        # 测试类型导入
        from litkit.druggability.ligandability import QueryBackend
        print("✓ 成功导入 QueryBackend 类型")
        
        print("\n✅ 所有导入测试通过！\n")
        return True
        
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def test_class_instantiation():
    """测试 ChemblLocalDB 类实例化"""
    print("=" * 60)
    print("测试 2: 类实例化测试")
    print("=" * 60)
    
    try:
        from litkit.druggability.chembl_local import ChemblLocalDB
        
        # 测试默认实例化
        db = ChemblLocalDB()
        print("✓ 默认实例化成功")
        
        # 测试带参数的实例化
        db2 = ChemblLocalDB(version="35", db_path="/tmp/test.db")
        print("✓ 带参数实例化成功")
        
        # 测试实例属性
        assert db.version == "36", "默认版本应该是 36"
        assert db2.version == "35", "版本应该是 35"
        print("✓ 实例属性正确")
        
        print("\n✅ 类实例化测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def test_ligandability_function_signatures():
    """测试 ligandability 函数签名"""
    print("=" * 60)
    print("测试 3: 函数签名测试")
    print("=" * 60)
    
    try:
        from litkit.druggability import assess_ligandability
        import inspect
        
        # 获取函数签名
        sig = inspect.signature(assess_ligandability)
        params = list(sig.parameters.keys())
        
        print(f"assess_ligandability 参数: {params}")
        
        # 验证关键参数
        assert 'query' in params, "应该有 query 参数"
        assert 'organism' in params, "应该有 organism 参数"
        assert 'backend' in params, "应该有 backend 参数"
        assert 'db' in params, "应该有 db 参数"
        print("✓ 函数签名正确")
        
        # 检查默认值
        backend_param = sig.parameters['backend']
        assert backend_param.default == 'auto', "backend 默认值应该是 'auto'"
        print(f"✓ backend 默认值: {backend_param.default}")
        
        print("\n✅ 函数签名测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def test_result_dataclass():
    """测试 LigandabilityResult 数据类"""
    print("=" * 60)
    print("测试 4: LigandabilityResult 数据类测试")
    print("=" * 60)
    
    try:
        from litkit.druggability.ligandability import LigandabilityResult
        
        # 创建实例
        result = LigandabilityResult(
            target_chembl_id="CHEMBL203",
            pref_name="EGFR",
            organism="Homo sapiens",
            n_known_ligands=100,
            n_approved_drugs=5,
            ligandability_score=0.8,
            backend_used="local"
        )
        
        print(f"✓ 创建 LigandabilityResult 实例")
        print(f"  target_chembl_id: {result.target_chembl_id}")
        print(f"  pref_name: {result.pref_name}")
        print(f"  n_known_ligands: {result.n_known_ligands}")
        print(f"  ligandability_score: {result.ligandability_score}")
        print(f"  backend_used: {result.backend_used}")
        
        # 测试 to_dict 方法
        result_dict = result.to_dict()
        assert 'backend_used' in result_dict, "to_dict 应该包含 backend_used"
        print(f"✓ to_dict 方法正确")
        
        print("\n✅ LigandabilityResult 数据类测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def test_score_mapping():
    """测试配体数量到分数的映射"""
    print("=" * 60)
    print("测试 5: 分数映射测试")
    print("=" * 60)
    
    try:
        from litkit.druggability.ligandability import _score_from_ligand_count
        
        test_cases = [
            (0, 0.0),
            (5, 0.2),
            (50, 0.6),
            (100, 0.8),
            (1500, 1.0),
        ]
        
        for n_ligands, expected_score in test_cases:
            score = _score_from_ligand_count(n_ligands)
            status = "✓" if score == expected_score else "✗"
            print(f"{status} n_ligands={n_ligands:5d} -> score={score} (expected {expected_score})")
            assert score == expected_score, f"映射错误: {n_ligands} -> {score} (expected {expected_score})"
        
        print("\n✅ 分数映射测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def test_comprehensive_assessment_function():
    """测试综合评估函数"""
    print("=" * 60)
    print("测试 6: 综合评估函数测试")
    print("=" * 60)
    
    try:
        from litkit.druggability import assess_druggability
        import inspect
        
        sig = inspect.signature(assess_druggability)
        params = list(sig.parameters.keys())
        
        print(f"assess_druggability 参数: {params}")
        
        # 验证新参数
        assert 'chembl_backend' in params, "应该有 chembl_backend 参数"
        assert 'chembl_db' in params, "应该有 chembl_db 参数"
        print("✓ 函数签名包含新的 ChEMBL 参数")
        
        chembl_backend_param = sig.parameters['chembl_backend']
        assert chembl_backend_param.default == 'auto', "chembl_backend 默认值应该是 'auto'"
        print(f"✓ chembl_backend 默认值: {chembl_backend_param.default}")
        
        print("\n✅ 综合评估函数测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("ChEMBL 本地数据库模块 - 功能测试")
    print("=" * 60 + "\n")
    
    tests = [
        test_imports,
        test_class_instantiation,
        test_ligandability_function_signatures,
        test_result_dataclass,
        test_score_mapping,
        test_comprehensive_assessment_function,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ 测试异常: {e}\n")
            failed += 1
    
    # 总结
    print("=" * 60)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！代码逻辑验证成功。\n")
        print("下一步：")
        print("1. 下载 ChEMBL 数据库 (需要约 5GB 空间)")
        print("2. 运行 examples/chembl_local_example.py 进行实际测试")
        print("\n提示：由于 ChEMBL 数据库下载速度较慢，建议：")
        print("- 使用稳定的网络连接")
        print("- 或使用国内镜像源")
        print("- 或手动下载后配置 db_path\n")
    else:
        print("\n⚠️ 部分测试失败，请检查代码。\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
