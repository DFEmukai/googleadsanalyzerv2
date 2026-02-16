"""Ad copy validation for Google Ads responsive search ads.

Validates headlines, descriptions, and URLs against Google Ads
character limits and formatting rules.
"""

import re
from typing import Any


class AdCopyValidationError(Exception):
    """Raised when ad copy validation fails with blocking errors."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Ad copy validation failed: {'; '.join(errors)}")


# Google Ads RSA limits
HEADLINE_MAX_LENGTH = 30
DESCRIPTION_MAX_LENGTH = 90
MIN_HEADLINES = 3
MAX_HEADLINES = 15
MIN_DESCRIPTIONS = 2
MAX_DESCRIPTIONS = 4
URL_PATTERN = re.compile(r"^https?://[^\s]+$")


def validate_ad_copy(
    headlines: list[str],
    descriptions: list[str],
    final_url: str,
) -> list[str]:
    """Validate ad copy content against Google Ads RSA rules.

    Args:
        headlines: List of headline texts
        descriptions: List of description texts
        final_url: The final URL for the ad

    Returns:
        List of warning messages (non-blocking issues)

    Raises:
        AdCopyValidationError: For blocking validation failures
    """
    errors: list[str] = []
    warnings: list[str] = []

    # --- Headlines validation ---
    if not headlines:
        errors.append("ヘッドラインが指定されていません")
    elif len(headlines) < MIN_HEADLINES:
        errors.append(
            f"ヘッドラインは最低{MIN_HEADLINES}本必要です "
            f"(現在: {len(headlines)}本)"
        )
    elif len(headlines) > MAX_HEADLINES:
        errors.append(
            f"ヘッドラインは最大{MAX_HEADLINES}本までです "
            f"(現在: {len(headlines)}本)"
        )

    for i, hl in enumerate(headlines):
        hl_stripped = hl.strip()
        if not hl_stripped:
            errors.append(f"ヘッドライン{i + 1}が空です")
            continue
        if len(hl_stripped) > HEADLINE_MAX_LENGTH:
            errors.append(
                f"ヘッドライン{i + 1}が{HEADLINE_MAX_LENGTH}文字を超えています "
                f"({len(hl_stripped)}文字): 「{hl_stripped}」"
            )
        elif len(hl_stripped) > HEADLINE_MAX_LENGTH - 3:
            warnings.append(
                f"ヘッドライン{i + 1}が上限に近いです "
                f"({len(hl_stripped)}/{HEADLINE_MAX_LENGTH}文字): 「{hl_stripped}」"
            )

    # Check for duplicate headlines
    seen_hl = set()
    for i, hl in enumerate(headlines):
        normalized = hl.strip().lower()
        if normalized in seen_hl:
            warnings.append(f"ヘッドライン{i + 1}が重複しています: 「{hl.strip()}」")
        seen_hl.add(normalized)

    # --- Descriptions validation ---
    if not descriptions:
        errors.append("説明文が指定されていません")
    elif len(descriptions) < MIN_DESCRIPTIONS:
        errors.append(
            f"説明文は最低{MIN_DESCRIPTIONS}本必要です "
            f"(現在: {len(descriptions)}本)"
        )
    elif len(descriptions) > MAX_DESCRIPTIONS:
        errors.append(
            f"説明文は最大{MAX_DESCRIPTIONS}本までです "
            f"(現在: {len(descriptions)}本)"
        )

    for i, desc in enumerate(descriptions):
        desc_stripped = desc.strip()
        if not desc_stripped:
            errors.append(f"説明文{i + 1}が空です")
            continue
        if len(desc_stripped) > DESCRIPTION_MAX_LENGTH:
            errors.append(
                f"説明文{i + 1}が{DESCRIPTION_MAX_LENGTH}文字を超えています "
                f"({len(desc_stripped)}文字)"
            )
        elif len(desc_stripped) > DESCRIPTION_MAX_LENGTH - 5:
            warnings.append(
                f"説明文{i + 1}が上限に近いです "
                f"({len(desc_stripped)}/{DESCRIPTION_MAX_LENGTH}文字)"
            )

    # --- URL validation ---
    if not final_url:
        errors.append("最終ページURLが指定されていません")
    elif not URL_PATTERN.match(final_url.strip()):
        errors.append(
            f"最終ページURLの形式が不正です: 「{final_url}」"
        )

    if errors:
        raise AdCopyValidationError(errors)

    return warnings


def validate_action_steps_structure(action_steps: dict[str, Any]) -> list[str]:
    """Validate the structure of ad_copy action_steps from Claude's output.

    Args:
        action_steps: The action_steps dict from a proposal

    Returns:
        List of warning messages

    Raises:
        AdCopyValidationError: For blocking structural issues
    """
    errors: list[str] = []

    if not isinstance(action_steps, dict):
        raise AdCopyValidationError(["action_stepsがオブジェクト形式ではありません"])

    if action_steps.get("type") != "ad_copy_change":
        raise AdCopyValidationError(
            [f"action_steps.type が 'ad_copy_change' ではありません: {action_steps.get('type')}"]
        )

    # Check required fields
    if not action_steps.get("ad_group_id"):
        errors.append("ad_group_id が指定されていません")

    proposed = action_steps.get("proposed_ad")
    if not proposed:
        errors.append("proposed_ad が指定されていません")
    elif not isinstance(proposed, dict):
        errors.append("proposed_ad がオブジェクト形式ではありません")
    else:
        headlines = proposed.get("headlines", [])
        descriptions = proposed.get("descriptions", [])
        final_url = proposed.get("final_url", "")

        if errors:
            raise AdCopyValidationError(errors)

        # Validate the actual copy content
        return validate_ad_copy(headlines, descriptions, final_url)

    if errors:
        raise AdCopyValidationError(errors)

    return []
