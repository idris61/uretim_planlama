# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

from .reorder import *
from .profile_stock_api import *
from .production_planning import *

# Legacy module-level APIs under uretim_planlama.uretim_planlama.api (module)
# Export selected functions so calls to
#   uretim_planlama.uretim_planlama.api.get_sales_order_details
# resolve correctly to the package namespace.
try:
    from .. import api as _root_api
    get_sales_order_details = _root_api.get_sales_order_details
    get_materials = _root_api.get_materials
except Exception:  # noqa: E722
    # If root api module is unavailable during certain contexts, skip binding.
    pass
