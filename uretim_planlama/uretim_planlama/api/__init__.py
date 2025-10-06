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
    # IMPORTANT: There is both a package named `api` (this directory) and a module file `api.py` at the
    # same level. Relative import `from .. import api` would resolve to this package again. To import
    # the sibling file `api.py`, load it explicitly from its file path.
    import os
    import importlib
    import importlib.util

    _pkg_dir = os.path.dirname(__file__)
    _app_dir = os.path.dirname(_pkg_dir)  # .../uretim_planlama/uretim_planlama/uretim_planlama
    _root_api_path = os.path.join(_app_dir, 'api.py')

    if os.path.exists(_root_api_path):
        _spec = importlib.util.spec_from_file_location('uretim_planlama_root_api', _root_api_path)
        _root_api = importlib.util.module_from_spec(_spec)
        assert _spec.loader is not None
        _spec.loader.exec_module(_root_api)

        # Re-export selected functions so calls to
        # uretim_planlama.uretim_planlama.api.<fn> resolve correctly
        if hasattr(_root_api, 'get_sales_order_details'):
            get_sales_order_details = _root_api.get_sales_order_details
        if hasattr(_root_api, 'get_materials'):
            get_materials = _root_api.get_materials
        if hasattr(_root_api, 'get_sales_orders_by_opti'):
            get_sales_orders_by_opti = _root_api.get_sales_orders_by_opti
        if hasattr(_root_api, 'get_bom_materials_by_sales_order'):
            get_bom_materials_by_sales_order = _root_api.get_bom_materials_by_sales_order
        if hasattr(_root_api, 'get_approved_opti_nos'):
            get_approved_opti_nos = _root_api.get_approved_opti_nos
except Exception:
    # If root api module is unavailable during certain contexts, skip binding.
    pass

# ---- Runtime loader and thin wrappers to avoid package/module name collision ----
def _load_root_api_module():
    """
    Loads the sibling api.py module explicitly from its file path to avoid the
    package/module name collision with this package directory.
    """
    import os
    import importlib.util
    pkg_dir = os.path.dirname(__file__)
    app_dir = os.path.dirname(pkg_dir)
    root_api_path = os.path.join(app_dir, 'api.py')
    if not os.path.exists(root_api_path):
        raise ImportError('root api.py not found at ' + root_api_path)
    spec = importlib.util.spec_from_file_location('uretim_planlama_root_api_runtime', root_api_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover
    frappe = None  # Allow import in non-Frappe contexts

def get_sales_orders_by_opti(opti):
    root_api = _load_root_api_module()
    return root_api.get_sales_orders_by_opti(opti)

def get_bom_materials_by_sales_order(sales_order=None, **kwargs):
    root_api = _load_root_api_module()
    return root_api.get_bom_materials_by_sales_order(sales_order=sales_order, **kwargs)

def get_approved_opti_nos():
    root_api = _load_root_api_module()
    return root_api.get_approved_opti_nos()

@frappe.whitelist(allow_guest=True) if frappe else (lambda f: f)
def get_sales_order_details(order_no):
    root_api = _load_root_api_module()
    return root_api.get_sales_order_details(order_no)

@frappe.whitelist(allow_guest=True) if frappe else (lambda f: f)
def get_materials(opti_no, sales_order):
    root_api = _load_root_api_module()
    return root_api.get_materials(opti_no, sales_order)

# --- Direct package-level implementation to avoid any import-time ambiguity ---
try:
    import frappe  # type: ignore
    from frappe import _  # type: ignore
except Exception:
    frappe = None  # type: ignore
    _ = lambda x: x  # type: ignore

@frappe.whitelist(allow_guest=True) if frappe else (lambda f: f)
def get_sales_orders_by_opti(opti):
    """
    Opti belgesindeki teslim edilmemiş satış siparişlerini döndürür.
    Paket/modül adı çakışmalarından etkilenmemesi için doğrudan bu pakette tanımlıdır.
    """
    try:
        opti_doc = frappe.get_doc("Opti", opti)
    except frappe.DoesNotExistError:
        frappe.throw(_(f"Opti [{opti}] not found"))
    except Exception as e:  # noqa: E722
        frappe.log_error(f"Opti fetch error: {e!s}")
        frappe.throw(_( "An error occured" ))
    return [so.sales_order for so in getattr(opti_doc, 'sales_orders', []) if not getattr(so, 'delivered', False)]
