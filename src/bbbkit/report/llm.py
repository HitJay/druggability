"""
bbbkit.report.llm — OpenAI 兼容 LLM 客户端

读取 .env 中的 OpenAI-like 配置 (MARKETPLACE_*)，封装一个带重试的
chat 接口，并提供面向可药性报告的高层叙述生成函数。

环境变量 (见 .env):
    MARKETPLACE_API_KEY        — API key (SECRET，绝不打印)
    MARKETPLACE_API_BASE_URL   — OpenAI 兼容 base url
    MARKETPLACE_MODEL_NAME     — 模型名
    API_TIMEOUT                — 单次请求超时秒数 (默认 60)
    API_MAX_RETRIES            — 最大重试次数 (默认 2)

设计原则: **优雅降级**。无 key / 网络失败 / SDK 缺失时，所有生成函数
回退到基于规则的模板文本，保证报告始终能产出 (不抛异常中断流程)。
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# .env 加载 (静默失败)
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001
    pass


@dataclass
class LLMConfig:
    """LLM 连接配置 (从环境变量加载)。"""

    api_key: str = ""
    base_url: str = ""
    model: str = ""
    timeout: float = 60.0
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "LLMConfig":
        def _f(name: str, default: float) -> float:
            try:
                return float(os.environ.get(name, "") or default)
            except (TypeError, ValueError):
                return default

        return cls(
            api_key=os.environ.get("MARKETPLACE_API_KEY", "").strip(),
            base_url=os.environ.get("MARKETPLACE_API_BASE_URL", "").strip(),
            model=os.environ.get("MARKETPLACE_MODEL_NAME", "").strip(),
            timeout=_f("API_TIMEOUT", 60.0),
            max_retries=int(_f("API_MAX_RETRIES", 2)),
        )

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)


class LLMClient:
    """OpenAI 兼容 chat 客户端，带优雅降级。"""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig.from_env()
        self._client: Any = None
        self._init_error: str | None = None
        if self.config.available:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
            except Exception as e:  # noqa: BLE001
                self._init_error = str(e)
                logger.warning("LLM client init failed: %s", e)
        else:
            self._init_error = "LLM 配置缺失 (MARKETPLACE_API_KEY/BASE_URL/MODEL_NAME)"

    @property
    def enabled(self) -> bool:
        return self._client is not None

    @property
    def status(self) -> str:
        if self.enabled:
            return f"LLM enabled (model={self.config.model})"
        return f"LLM disabled — fallback to templates ({self._init_error})"

    def chat(self, system: str, user: str, *, temperature: float | None = None, max_tokens: int = 1200) -> str | None:
        """单轮 chat。失败返回 None (调用方应回退模板)。

        temperature 默认 None（不发送）—— 部分新模型 (如 claude opus 4.x) 已废弃该参数，
        发送会 400。若显式传入且模型拒绝，自动剥离后重试一次。
        """
        if not self.enabled:
            return None

        base_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            base_kwargs["temperature"] = temperature

        try:
            resp = self._client.chat.completions.create(**base_kwargs)
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            # 参数被模型拒绝 (deprecated/unsupported) → 剥离可选参数重试一次
            if "deprecated" in msg or "unsupported" in msg or "temperature" in msg or "max_tokens" in msg:
                minimal = {"model": self.config.model, "messages": base_kwargs["messages"]}
                try:
                    resp = self._client.chat.completions.create(**minimal)
                    return (resp.choices[0].message.content or "").strip()
                except Exception as e2:  # noqa: BLE001
                    logger.warning("LLM chat retry failed: %s", e2)
                    return None
            logger.warning("LLM chat failed: %s", e)
            return None


# ─── 高层叙述生成 (面向可药性报告) ─────────────────────────────────────

_SYS_ANALYST = (
    "你是一位资深药物发现计算科学家，专长靶点可药性 (druggability) 评估。"
    "基于结构化的多维评分 (遗传学验证、tractability 模态分解、ligandability、结构口袋)，"
    "用简洁、专业、可执行的中文撰写分析。避免空话，给出明确的成药策略判断。"
    "不要编造数据中没有的数值；当方向性 (direction) 为 unresolved 时，明确指出这是待补充项。"
)


def _fallback_target_narrative(rec: dict[str, Any]) -> str:
    """无 LLM 时的规则模板叙述。"""
    g = rec.get("gene_name", "?")
    mod = {"small_molecule": "小分子", "antibody": "抗体", "protac": "PROTAC/降解剂"}.get(
        rec.get("best_modality", ""), rec.get("best_modality", "未知")
    )
    gs = rec.get("genetics_score")
    tb = rec.get("tractability_best")
    parts = [
        f"{g} 与 GWAS 性状 {rec.get('gwas_trait','')} 关联。",
        f"遗传学验证分 {gs}，可药性最优分 {tb}，推荐首选模态为{mod}。",
        f"综合判断：{rec.get('recommendation','N/A')}。",
    ]
    if rec.get("direction", "").startswith("unresolved"):
        parts.append("⚠️ 效应方向 (激动/拮抗) 尚未解析，为下一步关键补充项。")
    if tb is not None and tb < 0.6:
        parts.append("可药性偏低，提示可能为 PPI/无序靶点，建议优先考虑抗体或其他非小分子模态。")
    return " ".join(parts)


def _fallback_exec_summary(records: list[dict[str, Any]]) -> str:
    n = len(records)
    pri = [r["gene_name"] for r in records if str(r.get("recommendation", "")).startswith("Priority")]
    hard = [r["gene_name"] for r in records if str(r.get("recommendation", "")).startswith("Hard")]
    lines = [
        f"本批次共评估 {n} 个遗传学证据靶点。",
        f"建议优先立项 (Priority): {', '.join(pri) if pri else '无'}。",
        f"高验证但成药难 (需模态创新): {', '.join(hard) if hard else '无'}。",
        "所有靶点的 GWAS 效应方向尚待解析，是下一阶段的共性关键补充项。",
    ]
    return " ".join(lines)


def generate_target_narrative(client: LLMClient, rec: dict[str, Any]) -> str:
    """为单个靶点生成分析叙述 (LLM 优先，失败回退模板)。"""
    compact = {
        k: rec.get(k)
        for k in [
            "gene_name", "gene_id", "gwas_trait", "target_class", "top_disease",
            "top_therapeutic_areas", "genetics_score", "genetic_assoc_score",
            "direction", "tractability_best", "best_modality",
            "tract_SM", "tract_Ab", "tract_PROTAC",
            "ligandability_score", "n_known_ligands", "structure_score",
            "overall_score", "confidence", "recommendation",
        ]
    }
    user = (
        "以下是单个靶点的可药性评估数据 (JSON)。请用 3-5 句中文给出专业解读，"
        "包括：成药策略 (模态选择)、关键风险/未知项、下一步建议。\n\n"
        + json.dumps(compact, ensure_ascii=False, indent=2)
    )
    out = client.chat(_SYS_ANALYST, user, max_tokens=600)
    return out or _fallback_target_narrative(rec)


def generate_executive_summary(client: LLMClient, records: list[dict[str, Any]]) -> str:
    """为整批靶点生成执行摘要 (LLM 优先，失败回退模板)。"""
    rows = [
        {k: r.get(k) for k in ["gene_name", "gwas_trait", "genetics_score",
                               "tractability_best", "best_modality",
                               "overall_score", "recommendation"]}
        for r in records
    ]
    user = (
        "以下是一批靶点的可药性评估汇总 (JSON 数组)。请用中文写一段执行摘要 (5-8 句)："
        "概述整体格局、按二维 (遗传学验证 × 可药性) 给出分组与优先级建议、点出共性风险。\n\n"
        + json.dumps(rows, ensure_ascii=False, indent=2)
    )
    out = client.chat(_SYS_ANALYST, user, max_tokens=900)
    return out or _fallback_exec_summary(records)
