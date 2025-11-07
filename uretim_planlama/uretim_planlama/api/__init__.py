# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
API Module Exports
Bu modül tüm API fonksiyonlarını merkezi olarak export eder.
"""

import frappe

# Production Planning API
from uretim_planlama.uretim_planlama.api.production_planning import (
    get_daily_cutting_matrix,
    get_weekly_production_schedule,
)

# Profile Stock API  
from uretim_planlama.uretim_planlama.api.profile_stock_api import (
    get_profile_stock_panel,
)

# Cache Utils
from uretim_planlama.uretim_planlama.api.cache_utils import (
    clear_profile_groups_cache,
    get_cache_info,
)

# Profile Items
from uretim_planlama.uretim_planlama.api.profile_items import (
    get_profile_items_filter,
    get_profile_groups,
    refresh_profile_groups_cache,
)

# Import Pre-check
from uretim_planlama.uretim_planlama.api.import_pre_check import (
    check_existing_stock_before_import,
    get_import_summary_report,
)

# Parent api.py metodları için lazy loading
# NOT: api/__init__.py (bu dosya) ve api.py aynı parent'ta (uretim_planlama.uretim_planlama)
# Bu yüzden dikkatli import gerekiyor

_parent_api_cache = None

def _get_parent_api():
    """Parent api.py modülünü yükle ve cache'le"""
    global _parent_api_cache
    if _parent_api_cache is None:
        # Relative import ile parent api.py'yi yükle
        from .. import api as parent_api
        _parent_api_cache = parent_api
    return _parent_api_cache


# Parent API metodlarını lazy loading ile export et
def __getattr__(name):
    """
    Lazy import for parent api.py methods.
    Bu fonksiyon çağrıldığında parent api.py'den metodları yükler.
    """
    # Parent api.py'deki metodlar listesi
    # NOT: Bu metodlar artık kullanılmıyor, __getattr__ kaldırılacak
    parent_api_methods = []
    
    if name in parent_api_methods:
        parent_api = _get_parent_api()
        return getattr(parent_api, name)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Production Planning
    "get_daily_cutting_matrix",
    "get_weekly_production_schedule",
    # Profile Stock
    "get_profile_stock_panel",
    # Cache
    "clear_profile_groups_cache",
    "get_cache_info",
    # Profile Items
    "get_profile_items_filter",
    "get_profile_groups",
    "refresh_profile_groups_cache",
    # Import
    "check_existing_stock_before_import",
    "get_import_summary_report",
]
