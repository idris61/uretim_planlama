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
	
	NOT: ERPNext'in kendi update_completed_and_requested_qty fonksiyonu da çalışır.
	Bizim kodumuz SADECE custom_material_request_references field'ı olan itemlar için çalışır.
	Normal itemlar için ERPNext'in kendi kodu çalışır (çekirdek fonksiyon korunur).
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
	
	KALICI ÇÖZÜM: ordered_qty'yi EKLE (+=) değil, DOĞRU DEĞERE SET (=) eder.
	Böylece ERPNext'in kendi kodu ile çakışma olsa bile doğru sonuç çıkar.
	Çekirdek fonksiyonlar etkilenmez.
	
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
			# SADECE Stock Entry'deki item_code'lar için ordered_qty güncellenir
			
			# Her item_code için bu MR'nin orijinal qty'sini hesapla
			item_qty_map = {}
			for item_data in items_data:
				item_code = item_data["item_code"]
				if item_code not in item_qty_map:
					# Bu item_code için MR'deki orijinal stock_qty'yi al
					mr_item_qty = frappe.db.get_value(
						"Material Request Item",
						{"parent": mr_name, "item_code": item_code},
						"stock_qty"
					) or 0
					item_qty_map[item_code] = mr_item_qty
			
			if is_submit:
				# Submit: KALICI ÇÖZÜM - ordered_qty'yi SET et (EKLE değil!)
				# Tüm submitted SE'lerin toplam qty'sini hesapla ve SET et
				# Böylece ERPNext'in kodu 2x eklese bile doğru sonuç çıkar
				for item_code, original_qty in item_qty_map.items():
					# Bu MR ve item_code için TÜM submitted SE'lerin toplam qty'sini hesapla
					total_transferred = frappe.db.sql("""
					SELECT COALESCE(SUM(sed.qty), 0) as total
					FROM `tabStock Entry Detail` sed
					JOIN `tabStock Entry` se ON se.name = sed.parent
					WHERE se.docstatus = 1
						AND se.stock_entry_type = 'Material Transfer'
						AND sed.item_code = %s
						AND (sed.custom_material_request_references LIKE %s
							OR sed.material_request = %s)
				""", (item_code, f"%{mr_name}%", mr_name))[0][0] or 0
					
					# ordered_qty'yi doğru değere SET et (stock_qty'yi aşmasın)
					correct_qty = min(total_transferred, original_qty)
					
					frappe.db.sql("""
						UPDATE `tabMaterial Request Item`
						SET ordered_qty = %s
						WHERE parent = %s AND item_code = %s
					""", (correct_qty, mr_name, item_code))
			else:
				# Cancel: KALICI ÇÖZÜM - ordered_qty'yi SET et (AZALT değil!)
				# Kalan submitted SE'lerin toplam qty'sini hesapla ve SET et
				for item_code, original_qty in item_qty_map.items():
					# Bu SE hariç kalan submitted SE'lerin toplam qty'si
					total_transferred = frappe.db.sql("""
						SELECT COALESCE(SUM(sed.qty), 0) as total
						FROM `tabStock Entry Detail` sed
						JOIN `tabStock Entry` se ON se.name = sed.parent
						WHERE se.docstatus = 1
						AND se.name != %s
						AND se.stock_entry_type = 'Material Transfer'
						AND sed.item_code = %s
						AND (sed.custom_material_request_references LIKE %s
						OR sed.material_request = %s)
					""", (doc.name, item_code, f"%{mr_name}%", mr_name))[0][0] or 0
					
					# ordered_qty'yi doğru değere SET et
					correct_qty = min(total_transferred, original_qty)
					
					frappe.db.sql("""
						UPDATE `tabMaterial Request Item`
						SET ordered_qty = %s
						WHERE parent = %s AND item_code = %s
					""", (correct_qty, mr_name, item_code))
			
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
			# Material Transfer için doğru status isimleri
			if mr_doc.per_ordered >= 100:
				final_status = "Transferred"
			elif mr_doc.per_ordered > 0:
				final_status = "Partially Received"
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

