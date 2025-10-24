import frappe

def auto_wip_warehouse(doc, method):
    """Set WIP Warehouse automatically based on production item's item group.

    - If item group is "PVC", sets `wip_warehouse` to "PVC ÜRETİM DEPO - O"
    - If item group is "Camlar", sets `wip_warehouse` to "CAM ÜRETİM DEPO - O"
    """
    if not getattr(doc, "production_item", None):
        return

    item_group = frappe.db.get_value("Item", doc.production_item, "item_group")
    
    if item_group == "PVC":
        doc.wip_warehouse = "PVC ÜRETİM DEPO - O"
    elif item_group == "Camlar":
        doc.wip_warehouse = "CAM ÜRETİM DEPO - O"


