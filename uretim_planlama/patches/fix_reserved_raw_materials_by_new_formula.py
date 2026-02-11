"""
Patch: Re-scale existing Rezerved Raw Materials quantities to match the new
       reservation formula (only BOM quantity, without multiplying by
       Sales Order item quantity).

Amaç:
- Geçmişte, rezerv miktarı hesaplanırken BOM satır miktarı, satış siparişi
  satır miktarı ile ÇARPILIYORDU.
- Yeni mantıkta rezerv, sadece BOM'daki hammadde miktarı (rm_stock_qty)
  kadar olmalı; satış siparişi satır miktarı hesaba katılmamalı.
- Bu patch, mevcut Rezerved Raw Materials kayıtlarını yeni ölçeğe
  göre ORANSAL olarak düzeltir.

Mantık (her Sales Order + hammadde için):
- Eski toplam ihtiyaç:
    total_old = Σ (rm_stock_qty * item_stock_qty)
- Yeni toplam ihtiyaç:
    total_new = Σ (rm_stock_qty)
- Oran:
    ratio = total_new / total_old
- Mevcut rezerv miktarı da geçmişte total_old ölçeğinde yaratılıp
  aynı ölçekle tüketildiği için, doğru kalan miktar:
    corrected_qty = current_qty * ratio

Notlar:
- Sadece ratio anlamlı (0'dan büyük ve 1'e anlamlı uzaklıkta) ise
  güncelleme yapılır.
- Çok küçük yeni miktarlar (≈0) temizlenir.
"""

import frappe
from frappe.utils import flt


def get_real_qty(qty, precision=6):
    """Helper: None güvenli, flt tabanlı miktar normalizasyonu."""
    if qty is None:
        return flt(0, precision)
    return flt(qty, precision)


def execute():
    frappe.db.auto_commit_on_many_writes = True

    print("\n" + "=" * 80)
    print("REZERVED RAW MATERIALS - YENİ FORMÜLE GÖRE DÜZELTME BAŞLIYOR")
    print("=" * 80)

    try:
        # Rezervi olan tüm satış siparişlerini bul
        sales_orders = frappe.db.sql(
            """
            SELECT DISTINCT sales_order
            FROM `tabRezerved Raw Materials`
            WHERE IFNULL(sales_order, '') != ''
            """,
            as_dict=True,
        )

        print(f"Toplam {len(sales_orders)} satış siparişi için rezerv düzeltmesi denenecek.\n")

        processed_so = 0
        updated_rows = 0
        deleted_rows = 0

        for so_row in sales_orders:
            so_name = so_row.sales_order
            if not so_name:
                continue

            try:
                u_cnt, d_cnt = _fix_reserves_for_sales_order(so_name)
                processed_so += 1
                updated_rows += u_cnt
                deleted_rows += d_cnt
            except Exception as e:
                frappe.log_error(
                    f"Rezerv düzeltme hatası (Sales Order: {so_name})",
                    frappe.get_traceback(),
                )
                print(f"✗ {so_name}: {str(e)}")
                continue

        frappe.db.commit()

        print("\n" + "-" * 80)
        print("İŞLEM ÖZETİ")
        print("-" * 80)
        print(f"- İşlenen satış siparişi sayısı  : {processed_so}")
        print(f"- Güncellenen rezerv satırı      : {updated_rows}")
        print(f"- Silinen (≈0 kalan) rezerv satırı: {deleted_rows}")
        print("=" * 80 + "\n")

    except Exception:
        frappe.db.rollback()
        print("\n✗ Patch sırasında HATA oluştu, tüm değişiklikler geri alındı.")
        raise


def _fix_reserves_for_sales_order(sales_order: str) -> tuple[int, int]:
    """Tek bir satış siparişi için tüm hammaddeleri yeni formüle göre ölçekler."""
    try:
        so = frappe.get_doc("Sales Order", sales_order)
    except frappe.DoesNotExistError:
        # Satış siparişi silindiyse rezervleri dokunma (başka patch'ler temizleyebilir)
        return 0, 0

    # Sales Order satırlarından BOM'ları okuyup hammadde haritasını kur
    item_bom_map: dict[str, list[tuple[object, object]]] = {}

    for item in so.items:
        bom_name = frappe.db.get_value(
            "BOM",
            {"item": item.item_code, "is_active": 1, "is_default": 1},
            "name",
        )
        if not bom_name:
            continue

        bom_doc = frappe.get_doc("BOM", bom_name)
        for rm in bom_doc.items:
            # Sadece gerçek hammadde olanlar eklensin
            is_hammadde = frappe.db.get_value(
                "Item",
                rm.item_code,
                ["is_stock_item", "is_purchase_item"],
                as_dict=True,
            )
            if not is_hammadde or not (
                is_hammadde.is_stock_item and is_hammadde.is_purchase_item
            ):
                continue

            hammadde_code = str(rm.item_code).strip()
            item_bom_map.setdefault(hammadde_code, []).append((item, rm))

    if not item_bom_map:
        return 0, 0

    updated_rows = 0
    deleted_rows = 0

    # Her hammadde için eski ve yeni toplamı hesaplayıp, mevcut rezervi oransal düzelt
    for item_code, pairs in item_bom_map.items():
        total_bom_only = 0.0
        total_bom_times_so = 0.0

        for so_item, rm in pairs:
            rm_stock_qty = get_real_qty(
                rm.stock_qty
                if hasattr(rm, "stock_qty") and rm.stock_qty and rm.stock_qty > 0
                else rm.qty
            )
            item_stock_qty = get_real_qty(
                so_item.stock_qty
                if hasattr(so_item, "stock_qty")
                and so_item.stock_qty
                and so_item.stock_qty > 0
                else so_item.qty
            )

            total_bom_only += rm_stock_qty
            total_bom_times_so += rm_stock_qty * item_stock_qty

        # Geçersiz veya oransız durumlar için atla
        if total_bom_only <= 0 or total_bom_times_so <= 0:
            continue

        ratio = flt(total_bom_only / total_bom_times_so, 8)

        # 1'e çok yakınsa düzeltmeye gerek yok
        if abs(ratio - 1.0) < 0.000001:
            continue

        # İlgili Rezerved Raw Materials satırlarını çek
        rezerv_rows = frappe.get_all(
            "Rezerved Raw Materials",
            filters={"sales_order": sales_order, "item_code": item_code},
            fields=["name", "quantity"],
        )

        if not rezerv_rows:
            continue

        print(
            f"- Sales Order {sales_order} / Hammadde {item_code} için oran: "
            f"old_total={total_bom_times_so} → new_total={total_bom_only} (ratio={ratio})"
        )

        for row in rezerv_rows:
            old_qty = get_real_qty(row["quantity"], precision=6)
            new_qty = get_real_qty(old_qty * ratio, precision=6)

            if new_qty <= flt(0.000001, 6):
                # Kalan miktar neredeyse sıfırsa satırı sil
                frappe.db.sql(
                    """
                    DELETE FROM `tabRezerved Raw Materials`
                    WHERE name = %s
                    """,
                    (row["name"],),
                )
                deleted_rows += 1
                print(
                    f"   ✓ Silindi: {row['name']} "
                    f"(eski: {old_qty}, yeni ≈ 0; ratio={ratio})"
                )
            else:
                frappe.db.sql(
                    """
                    UPDATE `tabRezerved Raw Materials`
                    SET quantity = %s
                    WHERE name = %s
                    """,
                    (new_qty, row["name"]),
                )
                updated_rows += 1
                print(
                    f"   ✓ Güncellendi: {row['name']} "
                    f"(eski: {old_qty} → yeni: {new_qty}; ratio={ratio})"
                )

    return updated_rows, deleted_rows


if __name__ == "__main__":
    # Manuel test için çalıştırılabilir
    execute()

