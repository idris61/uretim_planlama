"""
Tüm Production Plan'ları detaylı analiz eder:
- Kapatılmış ama eksik üretim olan iş emirleri
- Tamamlanmış iş emri için tekrar oluşturulmuş iş emirleri
- Hatalı durumdaki planlar
"""
import frappe
from frappe.utils import flt


def execute():
	"""
	Tüm submitted Production Plan'ları detaylı analiz eder
	"""
	frappe.reload_doc("manufacturing", "doctype", "production_plan")
	
	# Tüm submitted production plan'ları al
	all_plans = frappe.get_all(
		"Production Plan",
		filters={"docstatus": 1},
		fields=["name", "status", "workflow_state", "total_planned_qty", "total_produced_qty"],
		order_by="name",
		limit=1000
	)
	
	print(f"Toplam {len(all_plans)} submitted Production Plan analiz ediliyor...\n")
	
	problematic_plans = []
	closed_wo_issues = []
	duplicate_wo_issues = []
	incomplete_wo_issues = []
	
	for pp in all_plans:
		try:
			pp_doc = frappe.get_doc("Production Plan", pp.name)
			
			# Tüm Work Order'ları al (iptal edilenler dahil)
			work_orders = frappe.get_all(
				"Work Order",
				filters={"production_plan": pp.name},
				fields=["name", "status", "qty", "produced_qty", "docstatus", "creation"],
				order_by="creation"
			)
			
			if not work_orders:
				continue
			
			# Work Order durumlarını analiz et
			wo_statuses = [wo.status for wo in work_orders]
			total_wo_count = len(work_orders)
			completed_count = sum(1 for status in wo_statuses if status == "Completed")
			closed_count = sum(1 for status in wo_statuses if status == "Closed")
			cancelled_count = sum(1 for status in wo_statuses if status == "Cancelled")
			active_wo_count = total_wo_count - cancelled_count
			
			# Aktif Work Order'lar (Closed/Stopped hariç)
			wo_status_for_completion = frappe.get_all(
				"Work Order",
				filters={
					"production_plan": pp.name,
					"status": ("not in", ["Closed", "Stopped"]),
					"docstatus": ("<", 2),
				},
				fields=["name", "status", "qty", "produced_qty"],
			)
			all_wo_completed = all(s == "Completed" for s in [wo.status for wo in wo_status_for_completion]) if wo_status_for_completion else False
			
			# Item kontrolü
			all_items_produced = all(
				abs(flt(d.planned_qty) - flt(d.produced_qty)) < 0.000001 
				for d in pp_doc.po_items
			) if pp_doc.po_items else False
			
			# Eğer tüm Work Order'lar tamamlandıysa, item'ları üretilmiş say
			if all_wo_completed and active_wo_count > 0:
				all_items_produced = True
			
			should_be_completed = all_items_produced and all_wo_completed
			
			# Sorun tespiti
			has_issues = False
			issues = []
			
			# 1. Kapatılmış ama eksik üretim olan iş emirleri
			closed_with_incomplete = []
			for wo in work_orders:
				if wo.status == "Closed":
					if flt(wo.qty) > flt(wo.produced_qty) + 0.000001:
						closed_with_incomplete.append({
							"wo": wo.name,
							"qty": wo.qty,
							"produced": wo.produced_qty,
							"missing": flt(wo.qty) - flt(wo.produced_qty)
						})
			
			if closed_with_incomplete:
				has_issues = True
				issues.append(f"Kapatılmış ama eksik üretim: {len(closed_with_incomplete)} WO")
				closed_wo_issues.append({
					"plan": pp.name,
					"status": pp.status,
					"workflow": pp.workflow_state,
					"wo_list": closed_with_incomplete
				})
			
			# 2. Aynı item için birden fazla tamamlanmış iş emri (duplicate)
			# Production Plan Item'lara göre grupla
			if pp_doc.po_items:
				item_wo_map = {}
				for wo in work_orders:
					if wo.status == "Completed":
						# Bu WO'nun hangi plan item'ına ait olduğunu bul
						wo_doc = frappe.get_doc("Work Order", wo.name)
						if wo_doc.production_plan_item:
							pp_item = frappe.get_value("Production Plan Item", wo_doc.production_plan_item, "item_code")
							if pp_item:
								if pp_item not in item_wo_map:
									item_wo_map[pp_item] = []
								item_wo_map[pp_item].append({
									"wo": wo.name,
									"qty": wo.qty,
									"produced": wo.produced_qty,
									"creation": wo.creation
								})
				
				# Aynı item için birden fazla tamamlanmış WO varsa
				duplicate_items = {item: wos for item, wos in item_wo_map.items() if len(wos) > 1}
				if duplicate_items:
					has_issues = True
					issues.append(f"Tekrar oluşturulmuş iş emirleri: {len(duplicate_items)} item")
					duplicate_wo_issues.append({
						"plan": pp.name,
						"status": pp.status,
						"workflow": pp.workflow_state,
						"duplicates": duplicate_items
					})
			
			# 3. Eksik üretim olan ama kapatılmış iş emirleri nedeniyle plan completed olmuyor
			if should_be_completed and pp.status != "Completed":
				has_issues = True
				issues.append("Tamamlanmış olmalı ama değil")
			
			# 4. Aktif Work Order'lar tamamlandı ama plan completed değil
			if all_wo_completed and active_wo_count > 0 and pp.status != "Completed":
				has_issues = True
				issues.append("Tüm WO tamamlandı ama plan completed değil")
			
			# 5. Eksik üretim olan iş emirleri
			incomplete_wos = []
			for wo in work_orders:
				if wo.status not in ["Closed", "Cancelled", "Stopped"] and wo.docstatus < 2:
					if flt(wo.qty) > flt(wo.produced_qty) + 0.000001:
						incomplete_wos.append({
							"wo": wo.name,
							"status": wo.status,
							"qty": wo.qty,
							"produced": wo.produced_qty,
							"missing": flt(wo.qty) - flt(wo.produced_qty)
						})
			
			if incomplete_wos and not all_wo_completed:
				has_issues = True
				issues.append(f"Eksik üretim: {len(incomplete_wos)} WO")
				incomplete_wo_issues.append({
					"plan": pp.name,
					"status": pp.status,
					"workflow": pp.workflow_state,
					"wo_list": incomplete_wos
				})
			
			if has_issues:
				problematic_plans.append({
					"name": pp.name,
					"status": pp.status,
					"workflow_state": pp.workflow_state,
					"total_wo": total_wo_count,
					"completed_wo": completed_count,
					"closed_wo": closed_count,
					"active_wo": active_wo_count,
					"all_items_produced": all_items_produced,
					"all_wo_completed": all_wo_completed,
					"should_be_completed": should_be_completed,
					"issues": issues
				})
		
		except Exception as e:
			frappe.log_error(
				title=f"Production Plan Analysis Error ({pp.name})",
				message=f"Hata: {str(e)}\nTraceback: {frappe.get_traceback()}"
			)
			print(f"❌ {pp.name}: Hata - {str(e)}")
	
	# Rapor
	print(f"\n{'='*80}")
	print("DETAYLI ANALİZ RAPORU")
	print(f"{'='*80}\n")
	
	print(f"Toplam kontrol edilen plan: {len(all_plans)}")
	print(f"Toplam sorunlu plan: {len(problematic_plans)}")
	print(f"Kapatılmış ama eksik üretim olan plan: {len(closed_wo_issues)}")
	print(f"Tekrar oluşturulmuş iş emri olan plan: {len(duplicate_wo_issues)}")
	print(f"Eksik üretim olan plan: {len(incomplete_wo_issues)}")
	
	if problematic_plans:
		print(f"\n{'='*80}")
		print("SORUNLU PLANLAR")
		print(f"{'='*80}\n")
		
		for pp in problematic_plans[:50]:  # İlk 50'yi göster
			print(f"\n📋 {pp['name']}")
			print(f"   Status: {pp['status']}, Workflow: {pp['workflow_state']}")
			print(f"   WO: Toplam={pp['total_wo']}, Tamamlandı={pp['completed_wo']}, Kapatılmış={pp['closed_wo']}, Aktif={pp['active_wo']}")
			print(f"   Durum: Items Produced={pp['all_items_produced']}, WO Completed={pp['all_wo_completed']}, Should Complete={pp['should_be_completed']}")
			print(f"   Sorunlar: {', '.join(pp['issues'])}")
	
	if closed_wo_issues:
		print(f"\n{'='*80}")
		print("KAPATILMIŞ AMA EKSİK ÜRETİM OLAN İŞ EMRİLERİ")
		print(f"{'='*80}\n")
		
		for issue in closed_wo_issues[:20]:  # İlk 20'yi göster
			print(f"\n⚠️  {issue['plan']} (Status: {issue['status']}, Workflow: {issue['workflow']})")
			for wo_info in issue['wo_list']:
				print(f"   WO {wo_info['wo']}: Planlanan={wo_info['qty']}, Üretilen={wo_info['produced']}, Eksik={wo_info['missing']:.2f}")
	
	if duplicate_wo_issues:
		print(f"\n{'='*80}")
		print("TEKRAR OLUŞTURULMUŞ İŞ EMRİLERİ")
		print(f"{'='*80}\n")
		
		for issue in duplicate_wo_issues[:20]:  # İlk 20'yi göster
			print(f"\n⚠️  {issue['plan']} (Status: {issue['status']}, Workflow: {issue['workflow']})")
			for item, wos in issue['duplicates'].items():
				print(f"   Item: {item} - {len(wos)} tamamlanmış WO:")
				for wo_info in wos:
					print(f"      WO {wo_info['wo']}: Qty={wo_info['qty']}, Produced={wo_info['produced']}, Oluşturulma={wo_info['creation']}")
	
	if incomplete_wo_issues:
		print(f"\n{'='*80}")
		print("EKSİK ÜRETİM OLAN İŞ EMRİLERİ")
		print(f"{'='*80}\n")
		
		for issue in incomplete_wo_issues[:20]:  # İlk 20'yi göster
			print(f"\n⚠️  {issue['plan']} (Status: {issue['status']}, Workflow: {issue['workflow']})")
			for wo_info in issue['wo_list']:
				print(f"   WO {wo_info['wo']} ({wo_info['status']}): Planlanan={wo_info['qty']}, Üretilen={wo_info['produced']}, Eksik={wo_info['missing']:.2f}")
	
	return {
		"total": len(all_plans),
		"problematic": len(problematic_plans),
		"closed_wo_issues": len(closed_wo_issues),
		"duplicate_wo_issues": len(duplicate_wo_issues),
		"incomplete_wo_issues": len(incomplete_wo_issues),
		"problematic_plans": problematic_plans[:100]  # İlk 100'ü döndür
	}

