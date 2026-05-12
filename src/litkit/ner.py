"""
生物医学实体识别 (NER) 模块
基于 PubTator3 API (免安装) + 可选 scispacy 本地模型
"""

from __future__ import annotations

import re
from typing import Any

import requests


# ── PubTator3 API (推荐，免安装) ──────────────────────────────────────
PUBTATOR_URL = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/annotate"


def annotate_with_pubtator(
    text: str,
    concepts: list[str] | None = None,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """用 PubTator3 API 对文本进行实体标注。

    Args:
        text: 待标注文本（建议 <= 5000 字符）
        concepts: 实体类型过滤，如 ["Gene", "Disease", "Chemical", "Species"]
                  None 则返回全部
        timeout: 请求超时

    Returns:
        list[dict]: 每个实体含 text, type, start, end, id 等
    """
    payload = {"text": text}
    try:
        resp = requests.post(
            PUBTATOR_URL,
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[ner] PubTator3 请求失败: {e}")
        return []

    entities = []
    for passage in data.get("passages", []):
        for ann in passage.get("annotations", []):
            ent_type = ann.get("infons", {}).get("type", "")
            if concepts and ent_type not in concepts:
                continue
            for loc in ann.get("locations", []):
                entities.append(
                    {
                        "text": ann.get("text", ""),
                        "type": ent_type,
                        "start": loc.get("offset", 0),
                        "end": loc.get("offset", 0) + loc.get("length", 0),
                        "id": ann.get("infons", {}).get("identifier", ""),
                    }
                )
    return entities


def annotate_pmids_pubtator(
    pmids: list[str],
    concepts: list[str] | None = None,
    timeout: int = 30,
) -> dict[str, list[dict[str, Any]]]:
    """用 PubTator3 API 对 PubMed 文章进行实体标注（按 PMID）。

    Args:
        pmids: PMID 列表
        concepts: 实体类型过滤
        timeout: 请求超时

    Returns:
        dict: {pmid: [entities]}
    """
    base = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson"
    results = {}
    for pmid in pmids:
        try:
            resp = requests.get(
                base,
                params={"pmids": pmid},
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            entities = []
            for passage in data.get("passages", []):
                for ann in passage.get("annotations", []):
                    ent_type = ann.get("infons", {}).get("type", "")
                    if concepts and ent_type not in concepts:
                        continue
                    entities.append(
                        {
                            "text": ann.get("text", ""),
                            "type": ent_type,
                            "id": ann.get("infons", {}).get("identifier", ""),
                        }
                    )
            results[pmid] = entities
        except Exception as e:
            print(f"[ner] PubTator3 PMID={pmid} 失败: {e}")
            results[pmid] = []
    return results


# ── 简单正则匹配（备用） ──────────────────────────────────────────────
# 药物/化合物常见模式
_DRUG_PATTERN = re.compile(
    r"\b[A-Z][a-z]*(?:inib|umab|asib|azole|amine|mycin|cillin|vastatin|pril|sartan|olol)\b"
)


def regex_drug_entities(text: str) -> list[str]:
    """简单正则匹配可能的药物名（INN 后缀）。"""
    return list(set(_DRUG_PATTERN.findall(text)))


# ── scispacy (可选，需额外安装) ──────────────────────────────────────
def extract_entities_scispacy(
    text: str,
    model_name: str = "en_core_sci_sm",
) -> list[dict[str, Any]]:
    """用 scispacy 模型提取生医实体。

    需先安装:
        pip install scispacy
        pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz

    Args:
        text: 待标注文本
        model_name: spacy 模型名

    Returns:
        list[dict]
    """
    try:
        import spacy

        nlp = spacy.load(model_name)
        doc = nlp(text)
        entities = []
        for ent in doc.ents:
            entities.append(
                {
                    "text": ent.text,
                    "type": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )
        return entities
    except ImportError:
        print("[ner] scispacy 未安装，请运行: pip install scispacy")
        return []
    except OSError:
        print(f"[ner] 模型 {model_name} 未安装")
        return []


if __name__ == "__main__":
    sample = (
        "EGFR inhibitor erlotinib shows druggability against non-small cell lung cancer. "
        "The KRAS G12C mutation is targeted by sotorasib."
    )
    print("=== PubTator3 ===")
    ents = annotate_with_pubtator(sample)
    for e in ents:
        print(f"  {e['type']:10s} | {e['text']}")

    print("\n=== Regex drugs ===")
    drugs = regex_drug_entities(sample)
    print(f"  {drugs}")
