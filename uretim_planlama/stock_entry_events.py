import frappe


def validate(doc, method=None):
	"""
	Stock Entry validate sırasında, material_request alanı dolu olan
	itemların MR referanslarını custom_material_request_references field'ına kaydet
	"""
	populate_material_request_references(doc)


def on_submit(doc, method=None):
	"""
	Stock Entry submit olduğunda, birleştirilmiş itemların
	Material Request referanslarını bulup transferred_qty'lerini artırır ve statuslerini günceller
	"""
	# ERPNext'in kendi işlemleri bittikten SONRA çalışması için after_commit kullan
	frappe.db.after_commit.add(lambda: update_material_request_statuses(doc, is_submit=True))


def on_cancel(doc, method=None):
	"""
	Stock Entry cancel olduğunda, Material Request transferred_qty'lerini azaltır
	ve statuslerini geri alır
	"""
	frappe.db.after_commit.add(lambda: update_material_request_statuses(doc, is_submit=False))


def populate_material_request_references(doc):
	"""
	Stock Entry Item'larının material_request alanından
	custom_material_request_references text field'ına kayıt ekler.
	Bu fonksiyon validate sırasında çalışır ve MR referanslarının
	merge işleminde kaybolmamasını sağlar.
	
	MR referansları virgülle ayrılmış string olarak saklanır: "MR-001, MR-002, MR-003"
	
	Args:
		doc: Stock Entry document
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
	Stock Entry Item'larındaki Material Request referanslarını bulup
	MR items'larının transferred_qty'sini ve MR statuslerini günceller
	
	Args:
		doc: Stock Entry document
		is_submit: True ise submit (transferred_qty artır), False ise cancel (transferred_qty azalt)
	"""
	if not doc.items:
		return
	
	# Sadece Material Transfer tipindeki stok hareketlerini işle
	if doc.stock_entry_type != "Material Transfer":
		return
	
	# MR'leri ve ilgili item bilgilerini topla: {mr_name: [(item_code, qty, transfer_qty), ...]}
	mr_item_data = {}
	
	for se_item in doc.items:
		item_code = se_item.item_code
		qty = se_item.qty or 0
		transfer_qty = se_item.transfer_qty or 0
		
		# Custom text field'dan MR referanslarını al
		mr_references_str = getattr(se_item, "custom_material_request_references", "") or ""
		
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
						"transfer_qty": transfer_qty
					})
		
		# Custom field boşsa, standart material_request field'ına bak
		else:
			old_mr = getattr(se_item, "material_request", None)
			if old_mr:
				if old_mr not in mr_item_data:
					mr_item_data[old_mr] = []
				mr_item_data[old_mr].append({
					"item_code": item_code,
					"qty": qty,
					"transfer_qty": transfer_qty
				})
	
	# Hiç MR referansı yoksa çık
	if not mr_item_data:
		return
	
	# Her MR için transferred_qty ve status güncelle
	updated_mrs = []
	failed_mrs = []
	
	for mr_name, items_data in mr_item_data.items():
		try:
			# MR'nin mevcut durumunu kontrol et
			mr_doc = frappe.get_doc("Material Request", mr_name)
			
			# Sadece submit edilmiş ve Material Transfer tipindeki MR'leri güncelle
			if mr_doc.docstatus != 1:
				frappe.log_error(
					f"Material Request {mr_name} submit edilmemiş (docstatus={mr_doc.docstatus}), status güncellenmedi",
					"Stock Entry MR Status Update"
				)
				continue
			
			if mr_doc.material_request_type != "Material Transfer":
				# Sadece Material Transfer tipindeki MR'leri işle
				continue
			
			# Cancel işleminde, eğer MR "Stopped" ise bırak
			if not is_submit and mr_doc.status == "Stopped":
				frappe.log_error(
					f"Material Request {mr_name} 'Stopped' durumunda, status güncellenmedi",
					"Stock Entry MR Status Update"
				)
				continue
			
			# MR Items'ların transferred_qty'sini güncelle
			# Submit: Tüm MR items'ın ordered_qty'sini stock_qty'ye eşitle (100% transferred)
			# Cancel: ordered_qty'yi sıfırla
			if is_submit:
				# Submit: Tüm MR'yi transferred say
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
				final_status = "Transferred"
			elif mr_doc.per_ordered > 0:
				final_status = "Partially Ordered"
			else:
				final_status = "Pending"
			
			# Önce Material Request'in kendi set_status metodunu çağır
			try:
				mr_doc.set_status(update=True)
			except:
				pass
			
			# Sonra bizim istediğimiz status'ü FORCE et
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
				"Stock Entry MR Status Update Error"
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

