/* Kod Yorumları: Türkçe */
/* Production Plan listview ayarları - workflow_state desteği */

frappe.listview_settings["Production Plan"] = {
	hide_name_column: true,
	add_fields: ["status", "workflow_state"],
	filters: [["status", "!=", "Closed"]],
	get_indicator: function (doc) {
		// Önce workflow_state'yi kontrol et, varsa onu göster
		if (doc.workflow_state) {
			const workflowState = doc.workflow_state;
			const stateMap = {
				"Yeni Plan": { label: __("Yeni Plan"), color: "red" },
				"OPT Bekliyor": { label: __("OPT Bekliyor"), color: "yellow" },
				"Onay Bekliyor": { label: __("Onay Bekliyor"), color: "orange" },
				"Düzenlenecek": { label: __("Düzenlenecek"), color: "red" },
				"Üretime Hazır": { label: __("Üretime Hazır"), color: "blue" },
				"Devam Ediyor": { label: __("Devam Ediyor"), color: "orange" },
				"Tamamlandı": { label: __("Tamamlandı"), color: "green" },
				"İptal Edildi": { label: __("İptal Edildi"), color: "gray" },
			};
			
			const state = stateMap[workflowState];
			if (state) {
				return [state.label, state.color, "workflow_state,=," + workflowState];
			}
			// Bilinmeyen workflow_state için varsayılan
			return [workflowState, "gray", "workflow_state,=," + workflowState];
		}
		
		// workflow_state yoksa status'u göster (geriye dönük uyumluluk)
		if (doc.status === "Submitted") {
			return [__("Not Started"), "orange", "status,=,Submitted"];
		} else {
			return [
				__(doc.status),
				{
					Draft: "red",
					"In Process": "orange",
					Completed: "green",
					"Material Requested": "yellow",
					Cancelled: "gray",
					Closed: "grey",
				}[doc.status] || "gray",
				"status,=," + doc.status,
			];
		}
	},
};

