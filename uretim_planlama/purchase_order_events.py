import frappe


def validate(doc, method=None):
	"""
	Purchase Order validate sırasında, material_request alanı dolu olan
	itemların MR referanslarını custom_material_request_references tablosuna kaydet
	"""
	populate_material_request_references(doc)


def on_submit(doc, method=None):
	"""
	Purchase Order submit olduğunda, birleştirilmiş itemların
	Material Request referanslarını bulup ordered_qty'lerini artırır ve statuslerini günceller
	"""
	# ERPNext'in kendi işlemleri bittikten SONRA çalışması için after_commit kullan
	frappe.db.after_commit.add(lambda: update_material_request_statuses(doc, is_submit=True))


def on_cancel(doc, method=None):
	"""
	Purchase Order cancel olduğunda, Material Request ordered_qty'lerini azaltır
	ve statuslerini geri alır
	"""
	frappe.db.after_commit.add(lambda: update_material_request_statuses(doc, is_submit=False))


def on_update_after_submit(doc, method=None):
	"""
	Purchase Order update edildikten sonra (submit sonrası) MR statuslerini kontrol et
	"""
	pass


def populate_material_request_references(doc):
	"""
	Purchase Order Item'larının material_request alanından
	custom_material_request_references text field'ına kayıt ekler.
	Bu fonksiyon validate sırasında çalışır ve MR referanslarının
	merge işleminde kaybolmamasını sağlar.
	
	MR referansları virgülle ayrılmış string olarak saklanır: "MR-001, MR-002, MR-003"
	
	Args:
		doc: Purchase Order document
	"""
	if not doc.items:
		return
	
	for item in doc.items:
		# Eğer material_request alanı doluysa
		mr_name = getattr(item, "material_request", None)
		if not mr_name:
			continue
		
		# Mevcut referansları al (virgülle ayrılmış string)
		existing_refs = getattr(item, "custom_material_request_references", "") or ""
		
		# String'i listeye çevir, boşlukları temizle
		existing_list = [x.strip() for x in existing_refs.split(",") if x.strip()]
		
		# Bu MR referansı zaten var mı kontrol et
		if mr_name not in existing_list:
			existing_list.append(mr_name)
		
		# Listeyi tekrar virgülle ayrılmış string'e çevir
		item.custom_material_request_references = ", ".join(existing_list)


def update_material_request_statuses(doc, is_submit=True):
	"""
	Purchase Order Item'larındaki Material Request referanslarını bulup
	MR items'larının ordered_qty'sini ve MR statuslerini günceller
	
	Args:
		doc: Purchase Order document
		is_submit: True ise submit (ordered_qty artır), False ise cancel (ordered_qty azalt)
	"""
	if not doc.items:
		return
	
	# MR'leri ve ilgili item bilgilerini topla: {mr_name: [(item_code, qty, stock_qty), ...]}
	mr_item_data = {}
	
	for po_item in doc.items:
		item_code = po_item.item_code
		qty = po_item.qty or 0
		stock_qty = po_item.stock_qty or 0
		
		# Custom text field'dan MR referanslarını al
		mr_references_str = getattr(po_item, "custom_material_request_references", "") or ""
		
		# Önce custom field'ı kontrol et
		if mr_references_str and mr_references_str.strip():
			# Virgülle ayrılmış string'i listeye çevir
			mr_list = [x.strip() for x in mr_references_str.split(",") if x.strip()]
			
			# Her MR için item bilgisini kaydet
			for mr_name in mr_list:
				if mr_name:
					if mr_name not in mr_item_data:
						mr_item_data[mr_name] = []
					mr_item_data[mr_name].append({
						"item_code": item_code,
						"qty": qty,
						"stock_qty": stock_qty
					})
		
		# Custom field boşsa, standart material_request field'ına bak
		else:
			old_mr = getattr(po_item, "material_request", None)
			if old_mr:
				if old_mr not in mr_item_data:
					mr_item_data[old_mr] = []
				mr_item_data[old_mr].append({
					"item_code": item_code,
					"qty": qty,
					"stock_qty": stock_qty
				})
	
	# Her MR için ordered_qty ve status güncelle
	updated_mrs = []
	failed_mrs = []
	
	for mr_name, items_data in mr_item_data.items():
		try:
			# MR'nin mevcut durumunu kontrol et
			mr_doc = frappe.get_doc("Material Request", mr_name)
			
			# Sadece submit edilmiş MR'leri güncelle (docstatus=1)
			if mr_doc.docstatus != 1:
				frappe.log_error(
					f"Material Request {mr_name} submit edilmemiş (docstatus={mr_doc.docstatus}), status güncellenmedi",
					"Purchase Order MR Status Update"
				)
				continue
			
			# Cancel işleminde, eğer MR "Stopped" ise bırak
			if not is_submit and mr_doc.status == "Stopped":
				frappe.log_error(
					f"Material Request {mr_name} 'Stopped' durumunda, 'Pending'e çevrilmedi",
					"Purchase Order MR Status Update"
				)
				continue
			
			# MR Items'ların ordered_qty'sini güncelle
			# Submit: Tüm MR items'ın ordered_qty'sini stock_qty'ye eşitle (100% ordered)
			# Cancel: ordered_qty'yi sıfırla
			if is_submit:
				# Submit: Tüm MR'yi ordered say
				frappe.db.sql("""
					UPDATE `tabMaterial Request Item`
					SET ordered_qty = stock_qty
					WHERE parent = %s
				""", (mr_name,))
			else:
				# Cancel: ordered_qty'leri sıfırla
				frappe.db.sql("""
					UPDATE `tabMaterial Request Item`
					SET ordered_qty = 0
					WHERE parent = %s
				""", (mr_name,))
			
			# per_ordered yüzdesini hesapla ve güncelle
			frappe.db.sql("""
				UPDATE `tabMaterial Request` mr
				SET per_ordered = (
					SELECT 
						CASE 
							WHEN SUM(stock_qty) > 0 
							THEN (SUM(ordered_qty) / SUM(stock_qty)) * 100
							ELSE 0
						END
					FROM `tabMaterial Request Item`
					WHERE parent = mr.name
				),
				modified = NOW()
				WHERE name = %s
			""", (mr_name,))
			
			# MR'yi reload et
			mr_doc.reload()
			
			# per_ordered'a göre status belirle
			if mr_doc.per_ordered >= 100:
				final_status = "Ordered"
			elif mr_doc.per_ordered > 0:
				final_status = "Partially Ordered"
			else:
				final_status = "Pending"
			
			# Önce Material Request'in kendi set_status metodunu çağır
			# Bu, ERPNext'in status_map'ine göre status belirler
			try:
				mr_doc.set_status(update=True)
			except:
				pass
			
			# Sonra bizim istediğimiz status'ü FORCE et
			# Çünkü ERPNext'in mekanizması per_ordered < 100 için "Ordered" vermez
			# Ama biz birleştirilmiş itemlar için tüm MR'leri "Ordered" saymak istiyoruz
			frappe.db.sql("""
				UPDATE `tabMaterial Request`
				SET status = %s, modified = NOW()
				WHERE name = %s AND docstatus = 1
			""", (final_status, mr_name))
			
			frappe.db.commit()
			
			updated_mrs.append(f"{mr_name} ({final_status})")
			
		except Exception as e:
			# Hata durumunda log'a yaz ama işlemi durdurma
			failed_mrs.append(mr_name)
			frappe.log_error(
				f"Material Request {mr_name} status güncellenirken hata oluştu: {str(e)}\n\n{frappe.get_traceback()}",
				"Purchase Order MR Status Update Error"
			)
	
	# Özet mesajı (submit sonrasında görünecek)
	if updated_mrs:
		action_text = "Submit" if is_submit else "Cancel"
		frappe.msgprint(
			f"Material Request statusleri güncellendi ({action_text}): {', '.join(updated_mrs)}",
			indicator="green" if is_submit else "blue"
		)
	
	if failed_mrs:
		frappe.msgprint(
			f"Bazı Material Request'ler güncellenemedi: {', '.join(failed_mrs)}. Detaylar için Error Log kontrol edin.",
			indicator="red"
		)

