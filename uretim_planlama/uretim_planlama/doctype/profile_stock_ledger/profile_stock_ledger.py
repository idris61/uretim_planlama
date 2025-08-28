# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import logging

# Logger kurulumu
logger = logging.getLogger(__name__)

class ProfileStockLedger(Document):
	def validate(self):
		"""Boy (m) ve Miktar girildiyse, Toplam Boy (m) otomatik hesapla"""
		if self.length and self.qty:
			self.total_length = float(self.length) * int(self.qty)
		else:
			self.total_length = 0
		
		# Stok uyarı kontrolü
		self.check_stock_alerts()
	
	def check_stock_alerts(self):
		"""Düşük stok uyarıları kontrol et"""
		if self.qty <= 5:
			frappe.msgprint(
				f"⚠️ Düşük stok uyarısı: {self.profile_type} {self.length}m profilden sadece {self.qty} adet kaldı!",
				title=_("Düşük Stok Uyarısı"),
				indicator="red" if self.qty <= 2 else "orange"
			)
	
	def after_insert(self):
		"""Yeni kayıt eklendikten sonra işlemler"""
		logger.info(f"Profile Stock Ledger yeni kayıt: {self.profile_type} {self.length}m {self.qty}adet")
	
	def after_save(self):
		"""Kayıt güncellendikten sonra işlemler"""
		logger.info(f"Profile Stock Ledger güncellendi: {self.profile_type} {self.length}m {self.qty}adet")
	
	def on_trash(self):
		"""Kayıt silinmeden önce işlemler"""
		logger.info(f"Profile Stock Ledger silindi: {self.profile_type} {self.length}m {self.qty}adet")

def update_profile_stock(profile_type, length, qty, action, is_scrap_piece=0):
    """
    Profil stoklarını günceller. action: 'in' (giriş) veya 'out' (çıkış)
    """
    try:
        filters = {"profile_type": profile_type, "length": length, "is_scrap_piece": is_scrap_piece}
        stock = frappe.get_all("Profile Stock Ledger", filters=filters, fields=["name", "qty", "total_length"])
        
        if stock:
            doc = frappe.get_doc("Profile Stock Ledger", stock[0].name)
            old_qty = doc.qty
            
            if action == "in":
                doc.qty += qty
                logger.info(f"Stok girişi: {profile_type} {length}m +{qty}adet (Eski: {old_qty}, Yeni: {doc.qty})")
            elif action == "out":
                doc.qty -= qty
                if doc.qty < 0:
                    frappe.throw(f"Yetersiz stok: {profile_type} {length}m profilden çıkış yapılamaz. Mevcut: {old_qty}, İstenen: {qty}")
                logger.info(f"Stok çıkışı: {profile_type} {length}m -{qty}adet (Eski: {old_qty}, Yeni: {doc.qty})")
            
            doc.total_length = doc.qty * doc.length
            
            if doc.qty == 0:
                doc.delete()
                logger.info(f"Stok sıfırlandı, kayıt silindi: {profile_type} {length}m")
            else:
                doc.save()
                logger.info(f"Stok güncellendi: {profile_type} {length}m {doc.qty}adet")
        else:
            if action == "in":
                doc = frappe.new_doc("Profile Stock Ledger")
                doc.profile_type = profile_type
                doc.length = length
                doc.qty = qty
                doc.is_scrap_piece = is_scrap_piece
                doc.total_length = qty * length
                doc.insert()
                logger.info(f"Yeni stok kaydı oluşturuldu: {profile_type} {length}m {qty}adet")
            else:
                frappe.throw(f"Stokta olmayan profilden çıkış yapılamaz: {profile_type} {length}m")
        
        return True
        
    except Exception as e:
        logger.error(f"Profile stock güncelleme hatası: {profile_type} {length}m {qty}adet {action} - Hata: {str(e)}")
        frappe.log_error(f"Profile Stock Update Error: {str(e)}", "Profile Stock Update Error")
        raise e

def get_profile_stock(profile_type=None):
    """
    Profil stoklarını (boy ve adet bazında) listeler.
    Performans için optimize edilmiş sorgu.
    """
    try:
        filters = {}
        if profile_type:
            filters["profile_type"] = profile_type
        
        # Performans için sadece gerekli alanları getir
        stocks = frappe.get_all(
            "Profile Stock Ledger",
            filters=filters,
            fields=["profile_type", "length", "qty", "total_length", "is_scrap_piece"],
            order_by="profile_type, length",
            limit=1000  # Performans için limit
        )
        
        logger.info(f"Profile stock sorgusu: {len(stocks)} kayıt getirildi")
        return stocks
        
    except Exception as e:
        logger.error(f"Profile stock getirme hatası: {str(e)}")
        frappe.log_error(f"Profile Stock Get Error: {str(e)}", "Profile Stock Get Error")
        return []

def get_profile_stock_summary(profile_type=None):
    """
    Profil stok özetini döndürür (performans optimize edilmiş)
    """
    try:
        filters = {}
        if profile_type:
            filters["profile_type"] = profile_type
        
        # SQL ile direkt hesaplama (performans için)
        sql_query = """
            SELECT 
                profile_type,
                SUM(qty) as total_qty,
                SUM(total_length) as total_length,
                COUNT(*) as length_varieties
            FROM `tabProfile Stock Ledger`
            WHERE is_scrap_piece = 0
        """
        
        if profile_type:
            sql_query += " AND profile_type = %s"
            params = [profile_type]
        else:
            params = []
        
        sql_query += " GROUP BY profile_type ORDER BY profile_type"
        
        summary_data = frappe.db.sql(sql_query, params, as_dict=True)
        
        # Genel toplamlar
        total_profiles = sum(item.total_qty for item in summary_data)
        total_length = sum(item.total_length for item in summary_data)
        
        summary = {
            "total_profiles": total_profiles,
            "total_length": total_length,
            "by_profile": {item.profile_type: {
                "qty": item.total_qty,
                "total_length": item.total_length,
                "length_varieties": item.length_varieties
            } for item in summary_data}
        }
        
        logger.info(f"Profile stock özeti oluşturuldu: {len(summary_data)} profil türü")
        return summary
        
    except Exception as e:
        logger.error(f"Profile stock özeti hatası: {str(e)}")
        frappe.log_error(f"Profile Stock Summary Error: {str(e)}", "Profile Stock Summary Error")
        return {}

def get_length_options(doctype):
    """
    Belirtilen doctype'ta length alanının options'ını alır
    """
    try:
        meta = frappe.get_meta(doctype)
        length_field = meta.get_field("length")
        if length_field and length_field.fieldtype == "Select":
            return [opt.strip() for opt in length_field.options.split('\n') if opt.strip()]
        return []
    except Exception as e:
        logger.error(f"Length options getirme hatası: {str(e)}")
        return []

def get_stock_alerts(threshold_qty=10):
    """
    Düşük stok uyarılarını döndürür
    """
    try:
        alerts = frappe.get_all(
            "Profile Stock Ledger",
            filters={"qty": ["<=", threshold_qty], "is_scrap_piece": 0},
            fields=["profile_type", "length", "qty", "total_length"],
            order_by="qty ASC"
        )
        
        logger.info(f"Stok uyarıları getirildi: {len(alerts)} adet")
        return alerts
        
    except Exception as e:
        logger.error(f"Stok uyarıları getirme hatası: {str(e)}")
        return []

def reconcile_profile_stock_with_entries(counts, posting_date=None):
    """
    Sayım sonrası fiili stok ile sistemdeki stok arasındaki farkı Profile Stock Ledger'da günceller.
    counts: [
        {"profile_type": "Profil-1", "length": 5, "qty": 8},
        {"profile_type": "Profil-1", "length": 6, "qty": 4},
        ...
    ]
    posting_date: Düzeltme belgeleri için kullanılacak tarih (opsiyonel)
    """
    errors = []
    success_count = 0
    
    try:
        for count in counts:
            try:
                # Mevcut stok kaydını bul
                filters = {
                    "profile_type": count["profile_type"],
                    "length": count["length"],
                    "is_scrap_piece": 0
                }
                
                existing_stock = frappe.get_all("Profile Stock Ledger", filters=filters, fields=["name", "qty"])
                
                if existing_stock:
                    # Mevcut kaydı güncelle
                    stock_doc = frappe.get_doc("Profile Stock Ledger", existing_stock[0].name)
                    old_qty = stock_doc.qty
                    stock_doc.qty = count["qty"]
                    stock_doc.total_length = count["qty"] * count["length"]
                    stock_doc.save()
                    
                    logger.info(f"Stok güncellendi: {count['profile_type']} {count['length']}m {old_qty}->{count['qty']}")
                    success_count += 1
                else:
                    # Yeni kayıt oluştur
                    new_stock = frappe.new_doc("Profile Stock Ledger")
                    new_stock.profile_type = count["profile_type"]
                    new_stock.length = count["length"]
                    new_stock.qty = count["qty"]
                    new_stock.total_length = count["qty"] * count["length"]
                    new_stock.is_scrap_piece = 0
                    new_stock.insert()
                    
                    logger.info(f"Yeni stok kaydı oluşturuldu: {count['profile_type']} {count['length']}m {count['qty']}adet")
                    success_count += 1
                    
            except Exception as e:
                error_msg = f"Profil: {count['profile_type']}, Boy: {count['length']}, Hata: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Stok güncelleme hatası: {error_msg}")
        
        # Sonuçları kullanıcıya bildir
        if errors:
            error_text = "\n".join(errors)
            frappe.msgprint(
                f"Stok güncelleme tamamlandı!\n\n"
                f"✅ Başarılı işlem: {success_count} adet\n"
                f"❌ Hatalı işlem: {len(errors)} adet\n\n"
                f"📋 Hata detayları:\n{error_text}",
                title=_("Stok Güncelleme Sonucu"),
                indicator="yellow" if errors else "green"
            )
        else:
            frappe.msgprint(
                f"✅ Stok güncelleme başarıyla tamamlandı!\n"
                f"📊 Toplam {success_count} adet kayıt güncellendi.",
                title=_("Stok Güncelleme Sonucu"),
                indicator="green"
            )
        
        logger.info(f"Stok güncelleme tamamlandı: {success_count} başarılı, {len(errors)} hatalı")
        
    except Exception as e:
        logger.error(f"Stok güncelleme genel hatası: {str(e)}")
        frappe.log_error(f"Profile Stock Reconciliation Error: {str(e)}", "Profile Stock Reconciliation Error")

def after_import(doc, method):
    """
    Import işlemi tamamlandıktan sonra otomatik olarak çalışır.
    Mevcut stok ile import edilen stok arasındaki farkı Profile Stock Ledger'da günceller.
    """
    try:
        # Import edilen verileri al
        imported_data = frappe.get_all(
            "Profile Stock Ledger",
            filters={"name": doc.name},
            fields=["profile_type", "length", "qty"]
        )
        
        if imported_data:
            logger.info(f"Import sonrası stok güncelleme: {len(imported_data)} kayıt")
            reconcile_profile_stock_with_entries(imported_data)
        
    except Exception as e:
        logger.error(f"Profile Stock Ledger after_import hatası: {str(e)}")
        frappe.log_error(f"Profile Stock Ledger after_import hatası: {str(e)}", "Profile Stock Ledger Import Error")
