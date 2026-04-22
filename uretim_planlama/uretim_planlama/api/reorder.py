import frappe
from frappe import _
from datetime import date, timedelta


def _get_reorder_rule(profile_type: str, length: float, warehouse: str | None):
	"""Boy Link'i virgül/nokta ile adlandırılmış olabilir. Olası ad varyantlarını dene."""
	candidates = set()
	# Doğrudan str
	candidates.add(str(length))
	# 1 ve 3 ondalık biçimleri
	candidates.add(f"{length:.1f}")
	candidates.add(f"{length:.3f}".rstrip('0').rstrip('.'))
	# Nokta/virgül dönüşümleri
	for s in list(candidates):
		candidates.add(s.replace('.', ','))
		candidates.add(s.replace(',', '.'))
	
	# Debug için log
	frappe.logger().info(f"Reorder rule search candidates for {profile_type} {length}: {candidates}")

	rules = frappe.get_all(
		"Profile Reorder Rule",
		filters={
			"item_code": profile_type,
			"length": ("in", list(candidates)),
			"active": 1,
		},
		fields=["name", "min_qty", "reorder_qty", "default_supplier", "length"],
		limit=1,
	)
	
	if rules:
		frappe.logger().info(f"Found reorder rule: {rules[0]}")
		return rules[0]
	else:
		frappe.logger().info(f"No reorder rule found for {profile_type} {length}")
		return None


def _check_draft_purchase_mr(profile_type: str, warehouse: str | None) -> bool:
	"""Check if there are any Draft (docstatus=0) Purchase Material Requests for this item."""
	try:
		filters = {
			"docstatus": 0,
			"material_request_type": "Purchase",
			"items.item_code": profile_type
		}
		
		if warehouse:
			filters["items.warehouse"] = warehouse
		
		# Draft MR var mı kontrol et
		draft_mrs = frappe.get_all(
			"Material Request",
			filters=filters,
			fields=["name"],
			limit=1
		)
		
		return len(draft_mrs) > 0
		
	except Exception as e:
		frappe.log_error(f"_check_draft_purchase_mr error: {str(e)}", "Reorder Check MR Error")
		return False


def _has_open_purchase_request(profile_type: str, length_boy: str | None) -> bool:
	"""
	Duplicate önleme:
	- Sadece Draft (docstatus=0) değil, Submit edilmiş ama hâlâ açık/pipeline'da olan MR'leri de dikkate al.
	- Boy bazında kontrol et (custom_profile_length_m = Boy link).
	"""
	try:
		conditions = [
			"mr.docstatus in (0, 1)",
			"mr.material_request_type = 'Purchase'",
			"mri.item_code = %(item_code)s",
		]
		values = {"item_code": profile_type}
		if length_boy:
			conditions.append("COALESCE(mri.custom_profile_length_m, '') = %(length_boy)s")
			values["length_boy"] = length_boy

		# Stopped / Cancelled gibi kapanmış statüleri hariç tut
		conditions.append("COALESCE(mr.status, '') NOT IN ('Stopped', 'Cancelled')")

		row = frappe.db.sql(
			f"""
			SELECT mr.name
			FROM `tabMaterial Request` mr
			INNER JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
			WHERE {' AND '.join(conditions)}
			LIMIT 1
			""",
			values,
			as_dict=True,
		)
		return bool(row)
	except Exception as e:
		frappe.log_error(f"_has_open_purchase_request error: {str(e)}", "Reorder Open MR Check Error")
		return False


def _create_material_request(profile_type: str, qty: float, warehouse: str | None, supplier: str | None, length: float = None, profile_qty: int = None):
	mr = frappe.new_doc("Material Request")
	mr.material_request_type = "Purchase"
	mr.schedule_date = date.today() + timedelta(days=1)
	
	# Profil için özel alanlar
	if supplier:
		mr.supplier = supplier
	
	# Profil işaretle (eğer custom field varsa)
	if hasattr(mr, 'is_profile_request'):
		mr.is_profile_request = 1
	if hasattr(mr, 'custom_is_profile_request'):
		mr.custom_is_profile_request = 1
	
	# Açıklama ekle
	mr.description = f"Profil Malzeme Talebi - {profile_type} {length}m"
	
	row = mr.append("items", {})
	row.item_code = profile_type
	row.qty = qty
	if warehouse:
		row.warehouse = warehouse
	
	# Profil için özel alanlar ekle
	if length:
		# Boy bilgisini description'a ekle
		row.description = f"Profil Boyu: {length}m"
		
		# Profil boy adedi ve boyu bilgilerini ekle
		if hasattr(row, 'custom_is_profile'):
			row.custom_is_profile = 1
		if hasattr(row, 'custom_profile_length_m'):
			# Güçlü boy kayıt bulma fonksiyonunu kullan
			from uretim_planlama.uretim_planlama.utils import get_or_create_boy_record
			boy_name = get_or_create_boy_record(length)
			if boy_name:
				row.custom_profile_length_m = boy_name
		if hasattr(row, 'custom_profile_length_qty') and profile_qty:
			row.custom_profile_length_qty = profile_qty
		
		# Eğer custom field'lar varsa onları da doldur
		if hasattr(row, 'custom_length'):
			row.custom_length = length
		if hasattr(row, 'custom_profile_length'):
			row.custom_profile_length = length
	
	# Profil işaretle (eğer custom field varsa)
	if hasattr(row, 'is_profile'):
		row.is_profile = 1
	if hasattr(row, 'custom_is_profile'):
		row.custom_is_profile = 1
	
	# Draft bırak: duplicate önleme (_has_open_purchase_request / draft kontrolü) daha sağlıklı çalışır.
	mr.insert(ignore_permissions=True)
	return mr.name


# test_reorder_for_profile fonksiyonu kaldırıldı - ensure_reorder_for_profile kullanılıyor


def profile_reorder_sweep():
	"""Scan all non-scrap stocks and trigger reorders when below threshold."""
	stocks = frappe.get_all(
		"Profile Stock Ledger",
		filters={"is_scrap_piece": 0},
		fields=["item_code", "length", "qty"],
		limit=10000,
	)
	created = 0
	for s in stocks:
		try:
			mr = ensure_reorder_for_profile(s["item_code"], float(s["length"]), float(s["qty"]))
			if mr:
				created += 1
		except Exception as e:
			frappe.log_error(f"Reorder sweep error: {s} -> {e}", "Profile Reorder Sweep Error")
	return created


def ensure_reorder_for_profile(profile_type: str, length: float, current_qty: float, warehouse: str | None = None):
	"""Profile stok güncellemesi sonrası otomatik reorder kontrolü yapar."""
	try:
		# Debug log
		frappe.logger().info(f"ensure_reorder_for_profile: {profile_type} {length}m -> {current_qty} adet")
		
		# Reorder kuralı var mı kontrol et
		rule = _get_reorder_rule(profile_type, length, warehouse)
		if not rule:
			frappe.logger().info(f"No reorder rule for {profile_type} {length}m")
			return None

		# Boy bazında (Link) değer: duplicate kontrolünde bunu kullanacağız
		length_boy = rule.get("length")
		
		# Minimum stok kontrolü
		min_qty = float(rule.get("min_qty", 0))
		if current_qty >= min_qty:
			frappe.logger().info(f"Stock sufficient: {current_qty} >= {min_qty}")
			return None
		
		# Zaten açık (draft veya submitted) MR var mı kontrol et (boy bazında)
		if _has_open_purchase_request(profile_type, length_boy):
			frappe.logger().info(f"Open MR already exists for {profile_type} length={length_boy}")
			return None
		
		# Malzeme talebi oluştur
		reorder_qty = float(rule.get("reorder_qty", 0))
		if reorder_qty <= 0:
			frappe.logger().info(f"Invalid reorder quantity: {reorder_qty}")
			return None
		
		mr_name = _create_material_request(
			profile_type,
			reorder_qty,
			None,  # warehouse yok
			rule.get("default_supplier"),
			length,
			int(reorder_qty)  # profile_qty parametresi
		)
		
		# Son talep tarihini güncelle
		frappe.db.set_value("Profile Reorder Rule", rule["name"], "last_request_on", frappe.utils.now())
		
		frappe.logger().info(f"Material Request created: {mr_name} for {profile_type} {length}m")
		return mr_name
		
	except Exception as e:
		frappe.log_error(f"ensure_reorder_for_profile error: {profile_type} {length}m -> {str(e)}", "Profile Reorder Ensure Error")
		return None
