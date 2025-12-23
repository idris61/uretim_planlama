from frappe import _


def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    context.title = _("Depo Bazında Stok Değeri")


