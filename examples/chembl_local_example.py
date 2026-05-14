#!/usr/bin/env python3
"""
示例：使用 ChEMBL 本地数据库进行可药性评估

这个示例展示了如何使用本地 SQLite 数据库替代不稳定的 ChEMBL API。
"""

import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """基本用法示例"""
    print("=" * 60)
    print("示例 1: 基本用法 - 自动选择后端")
    print("=" * 60)
    
    try:
        from litkit.druggability import assess_ligandability
        
        # 使用 auto 模式（默认），优先本地数据库，失败则回退到 API
        result = assess_ligandability("EGFR", backend="auto")
        
        print(f"\n查询靶点: EGFR")
        print(f"ChEMBL ID: {result.target_chembl_id}")
        print(f"使用的后端: {result.backend_used}")
        print(f"已知配体数量: {result.n_known_ligands}")
        print(f"已批准药物数量: {result.n_approved_drugs}")
        print(f"Ligandability 分数: {result.ligandability_score}")
        
        if result.strongest_activity:
            print(f"\n最强活性:")
            print(f"  类型: {result.strongest_activity['type']}")
            print(f"  值: {result.strongest_activity['value']} {result.strongest_activity['unit']}")
        
        if result.top_compounds:
            print(f"\n前 {len(result.top_compounds)} 个化合物: {', '.join(result.top_compounds)}")
            
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请先运行: pip install -e .")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False
    
    return True


def example_force_local():
    """强制使用本地数据库示例"""
    print("\n" + "=" * 60)
    print("示例 2: 强制使用本地数据库")
    print("=" * 60)
    
    try:
        from litkit.druggability import assess_ligandability
        from litkit.druggability import chembl_local
        
        # 获取或创建数据库实例
        # 注意：首次运行时会下载 ChEMBL 数据库（约 1-2GB），需要一些时间
        print("\n提示：首次使用本地数据库会自动下载，需要一些时间...")
        
        try:
            # 尝试使用本地数据库
            result = assess_ligandability("BRAF", backend="local")
            
            print(f"\n查询靶点: BRAF")
            print(f"ChEMBL ID: {result.target_chembl_id}")
            print(f"使用的后端: {result.backend_used}")
            print(f"已知配体数量: {result.n_known_ligands}")
            print(f"Ligandability 分数: {result.ligandability_score}")
            
        except ImportError:
            print("\nchembl-downloader 未安装，无法使用本地数据库")
            print("请运行: pip install chembl-downloader")
            return False
        except Exception as e:
            print(f"\n本地数据库查询失败: {e}")
            print("可能需要先下载数据库，或检查网络连接")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    
    return True


def example_custom_db():
    """自定义数据库配置示例"""
    print("\n" + "=" * 60)
    print("示例 3: 自定义数据库配置")
    print("=" * 60)
    
    try:
        from litkit.druggability import chembl_local
        
        # 创建自定义配置的数据库实例
        print("\n创建自定义数据库实例...")
        
        # 可选配置：
        # - version: ChEMBL 版本（默认 "36"）
        # - db_path: 自定义数据库文件路径
        # - data_dir: 数据存储目录
        
        db = chembl_local.ChemblLocalDB(
            version="36",
            # db_path="/path/to/your/chembl.db",
            # data_dir="/path/to/data/dir"
        )
        
        print("数据库实例创建成功")
        
        # 可以直接使用 db 的方法
        print("\n直接使用数据库方法查询...")
        target_info = db.search_target("KRAS")
        
        if target_info:
            print(f"找到靶点: {target_info['pref_name']}")
            print(f"ChEMBL ID: {target_info['target_chembl_id']}")
            
            n_ligands, top_compounds = db.count_ligands(target_info['target_chembl_id'])
            print(f"配体数量: {n_ligands}")
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    
    return True


def example_comprehensive():
    """综合可药性评估示例"""
    print("\n" + "=" * 60)
    print("示例 4: 综合可药性评估（使用本地数据库）")
    print("=" * 60)
    
    try:
        from litkit.druggability import assess_druggability
        
        print("\n对靶点进行综合评估...")
        
        # 使用本地数据库进行 ChEMBL 查询
        result = assess_druggability(
            "EGFR",
            query_type="gene_symbol",
            chembl_backend="local"  # 指定使用本地数据库
        )
        
        print(f"\n综合评估结果:")
        print(f"查询: {result['query']}")
        
        if 'composite' in result:
            print(f"综合分数: {result['composite']['overall_score']}")
            print(f"置信度: {result['composite']['confidence']}")
            print(f"可用维度: {result['composite']['dimensions_available']}")
            
        if 'ligandability' in result and 'error' not in result['ligandability']:
            lig = result['ligandability']
            print(f"\nLigandability:")
            print(f"  分数: {lig['ligandability_score']}")
            print(f"  使用的后端: {lig.get('backend_used', 'unknown')}")
            
    except Exception as e:
        print(f"错误: {e}")
        return False
    
    return True


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("ChEMBL 本地数据库使用示例")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    # 示例 1
    total_count += 1
    if example_basic_usage():
        success_count += 1
    
    # 示例 2
    total_count += 1
    if example_force_local():
        success_count += 1
    
    # 示例 3
    total_count += 1
    if example_custom_db():
        success_count += 1
    
    # 示例 4
    total_count += 1
    if example_comprehensive():
        success_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print(f"示例完成: {success_count}/{total_count} 成功")
    print("=" * 60)
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
