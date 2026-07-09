"""
OME 中文 prompt 补丁 — 在服务器启动时自动将 everalgo 的英文 prompt
替换为中文版本，无需修改 everalgo 包。

生效条件：settings.memorize.prompt_lang == "zh"（默认）
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def apply_zh_prompts() -> None:
    """Monkey-patch everalgo prompt constants with Chinese versions."""

    # ── 1. 替换 episode extraction prompt ────────────────────────
    try:
        from everalgo.user_memory.prompts.en import episode as en_ep
        from everalgo.user_memory.prompts.zh import episode as zh_ep

        old_ep = en_ep.EPISODE_GENERATION_PROMPT
        old_uep = en_ep.USER_EPISODE_GENERATION_PROMPT
        en_ep.EPISODE_GENERATION_PROMPT = zh_ep.EPISODE_GENERATION_PROMPT
        en_ep.USER_EPISODE_GENERATION_PROMPT = zh_ep.USER_EPISODE_GENERATION_PROMPT
        logger.info("zh_patch: episode prompts switched to Chinese (was %d chars → now %d chars)",
                     len(old_ep), len(zh_ep.EPISODE_GENERATION_PROMPT))
    except Exception as e:
        logger.warning("zh_patch: episode prompt switch failed: %s", e)

    # ── 2. 替换 atomic_fact extraction prompt ────────────────────
    try:
        from everalgo.user_memory.prompts.en import atomic_fact as en_af
        from everalgo.user_memory.prompts.zh import atomic_fact as zh_af

        old_af = en_af.ATOMIC_FACT_PROMPT
        en_af.ATOMIC_FACT_PROMPT = zh_af.ATOMIC_FACT_PROMPT
        logger.info("zh_patch: atomic_fact prompt switched to Chinese")
    except Exception as e:
        logger.warning("zh_patch: atomic_fact prompt switch failed: %s", e)

    # ── 3. 替换 atomic_fact_from_text prompt（没有 zh 版，基于 zh ATOMIC_FACT_PROMPT 改造）──
    try:
        from everalgo.user_memory.prompts.en import atomic_fact_from_text as en_aft
        from everalgo.user_memory.prompts.zh import atomic_fact as zh_af

        # zh 版 ATOMIC_FACT_PROMPT 用 {INPUT_TEXT} 和 {TIME} 占位符
        # aextract_from_text 用 {{EPISODE_TEXT}} 占位符，需要适配
        # 直接用 zh prompt 改造占位符
        zh_text = zh_af.ATOMIC_FACT_PROMPT.replace("{INPUT_TEXT}", "{{EPISODE_TEXT}}")
        old_aft = en_aft.ATOMIC_FACT_FROM_TEXT_PROMPT_EN
        en_aft.ATOMIC_FACT_FROM_TEXT_PROMPT_EN = zh_text
        logger.info("zh_patch: atomic_fact_from_text prompt switched to Chinese")
    except Exception as e:
        logger.warning("zh_patch: atomic_fact_from_text prompt switch failed: %s", e)

    # ── 4. 替换 foresight extraction prompt ──────────────────────
    try:
        from everalgo.user_memory.prompts.en import foresight as en_fs
        from everalgo.user_memory.prompts.zh import foresight as zh_fs

        en_fs.FORESIGHT_GENERATION_PROMPT = zh_fs.FORESIGHT_GENERATION_PROMPT
        logger.info("zh_patch: foresight prompt switched to Chinese")
    except Exception as e:
        logger.warning("zh_patch: foresight prompt switch failed: %s", e)

    # ── 5. 替换 profile extraction prompt ────────────────────────
    try:
        from everalgo.user_memory.prompts.en import profile as en_pf
        from everalgo.user_memory.prompts.zh import profile as zh_pf

        en_pf.PROFILE_INITIAL_EXTRACTION_PROMPT = zh_pf.PROFILE_INITIAL_EXTRACTION_PROMPT
        en_pf.PROFILE_UPDATE_PROMPT = zh_pf.PROFILE_UPDATE_PROMPT
        logger.info("zh_patch: profile prompts switched to Chinese")
    except Exception as e:
        logger.warning("zh_patch: profile prompt switch failed: %s", e)

    # ── 6. 替换 reflect prompt ───────────────────────────────────
    try:
        from everalgo.user_memory.prompts.en import reflect as en_ref
        from everalgo.user_memory.prompts.zh import reflect as zh_ref

        en_ref.REFLECT_EPISODE_PROMPT = zh_ref.REFLECT_EPISODE_PROMPT
        if hasattr(zh_ref, "REFLECT_EPISODE_UPDATE_PROMPT"):
            en_ref.REFLECT_EPISODE_UPDATE_PROMPT = zh_ref.REFLECT_EPISODE_UPDATE_PROMPT
        logger.info("zh_patch: reflect prompts switched to Chinese")
    except Exception as e:
        logger.warning("zh_patch: reflect prompt switch failed: %s", e)

    # ── 7. 替换 boundary detection prompt ────────────────────────
    try:
        from everalgo.boundary.prompts.en import chat as en_bc
        from everalgo.boundary.prompts.zh import chat as zh_bc

        en_bc.BATCH_BOUNDARY_DETECT_PROMPT_EN = zh_bc.CHAT_BOUNDARY_DETECT_PROMPT_ZH
        en_bc.STEP_BOUNDARY_DETECT_PROMPT_EN = zh_bc.CHAT_BOUNDARY_DETECT_PROMPT_ZH
        logger.info("zh_patch: boundary detection prompts switched to Chinese")
    except Exception as e:
        logger.warning("zh_patch: boundary prompt switch failed: %s", e)

    logger.info("zh_patch: all OME prompts switched to Chinese")


def should_apply_zh() -> bool:
    """Check if the config says to use Chinese prompts."""
    try:
        from everos.config.settings import Settings
        settings = Settings()
        return settings.memorize.prompt_lang == "zh"
    except Exception:
        # If settings can't be loaded (e.g. during build), default to True
        return True
