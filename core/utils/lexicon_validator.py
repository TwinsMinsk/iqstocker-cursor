"""Validator for lexicon keys to prevent KeyError at runtime."""

from typing import List, Set
from bot.lexicon.lexicon_ru import LEXICON_RU

# Define all required keys for different modules
REQUIRED_KEYS = {
    'analytics': [
        'final_analytics_report',
        'analytics_explanation_title',
        'sold_portfolio_report',
        'new_works_report',
        'upload_limit_report',
        'analytics_closing_message',
        'upload_csv_prompt',
        'csv_instruction',
        'ask_portfolio_size',
        'ask_monthly_limit',
        'ask_monthly_uploads',
        'ask_profit_percentage',
        'ask_content_type',
        'processing_csv',
        'analytics_list_title',
        'analytics_unavailable',
    ],
    'recommendations': [
        'portfolio_rate_very_low',
        'portfolio_rate_low',
        'portfolio_rate_good',
        'portfolio_rate_very_good',
        'portfolio_rate_excellent',
        'new_work_rate_low',
        'new_work_rate_good',
        'new_work_rate_excellent',
        'new_work_rate_super',
        'new_work_rate_full',
        'upload_limit_0_30',
        'upload_limit_30_60',
        'upload_limit_61_80',
        'upload_limit_81_95',
        'upload_limit_97_100',
        # acceptance_rate keys removed - indicator excluded from reports
        'sold_portfolio_0_1_newbie',
        'sold_portfolio_1_2',
        'sold_portfolio_2_3',
        'sold_portfolio_3_5',
        'sold_portfolio_5_plus',
        # New works keys (ID-based logic)
        'new_works_0_10_newbie',
        'new_works_10_20',
        'new_works_20_30',
        'new_works_30_85',
        'new_works_85_100',
    ]
}

def validate_lexicon_keys() -> List[str]:
    """Validate that all required keys exist in LEXICON_RU."""
    missing_keys = []
    
    for category, keys in REQUIRED_KEYS.items():
        for key in keys:
            if key not in LEXICON_RU:
                missing_keys.append(f"{category}.{key}")
    
    return missing_keys

def validate_or_raise():
    """Validate lexicon keys and raise exception if any are missing."""
    missing = validate_lexicon_keys()
    if missing:
        raise KeyError(
            f"Missing {len(missing)} required lexicon keys:\n" + 
            "\n".join(f"  - {k}" for k in missing)
        )
