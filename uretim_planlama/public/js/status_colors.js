// Tüm durum renkleri ve etiketleri burada tanımlanıyor
frappe.provide('uretim_planlama');

if (!uretim_planlama.status_colors) {
	uretim_planlama.status_colors = {
		// Ana durum renkleri
		statusBadges: {
			'Draft':        { bg: '#9e9e9e', color: '#fff', label: 'Taslak' },
			'Submitted':    { bg: '#ffd600', color: '#333', label: 'Gönderildi' },
			'Not Started':  { bg: '#ffd600', color: '#333', label: 'Başlamadı' },
			'In Process':   { bg: '#ff9800', color: '#fff', label: 'İşlemde' },
			'Completed':    { bg: '#4caf50', color: '#fff', label: 'Tamamlandı' },
			'Stopped':      { bg: '#f44336', color: '#fff', label: 'Durduruldu' },
			'Closed':       { bg: '#9e9e9e', color: '#fff', label: 'Kapatıldı' },
			'Cancelled':    { bg: '#f44336', color: '#fff', label: 'İptal Edildi' },
			'Pending':      { bg: '#ffd600', color: '#333', label: 'Beklemede' },
			'Open':         { bg: '#ffd600', color: '#333', label: 'Açık' },
			'Work In Progress': { bg: '#ff9800', color: '#fff', label: 'Devam Ediyor' },
			'Material Transferred': { bg: '#ffd600', color: '#333', label: 'Malzeme Aktarıldı' },
			'On Hold':      { bg: '#9e9e9e', color: '#fff', label: 'Durduruldu' }
		},

		// Operasyon durumları için özel renkler (varsayılan olarak ana durum renklerini kullanır)
		operationStatusBadges: {
			// Operasyonlar için özel durumlar buraya eklenebilir
			// Şu an için ana durum renklerini kullanıyor
		},

		// Yardımcı fonksiyonlar
		getStatusBadge: function(status) {
			if (!status) return { bg: '#9e9e9e', color: '#fff', label: 'Bilinmiyor' };
			return this.statusBadges[status] || { bg: '#9e9e9e', color: '#fff', label: status };
		},

		getOperationStatusBadge: function(status) {
			if (!status) return { bg: '#9e9e9e', color: '#fff', label: 'Bilinmiyor' };
			return this.operationStatusBadges[status] || this.statusBadges[status] || { bg: '#9e9e9e', color: '#fff', label: status };
		}
	};
} 