// Hammadde Eksikleri Takip Sayfası
// Satınalma personeli için tüm siparişlere ait hammadde eksiklerini gösterir

// Socket.io hatalarını console'da gösterme - bu sayfa için gerekli değil
(function() {
	const originalError = console.error;
	console.error = function(...args) {
		// Socket.io bağlantı hatalarını filtrele
		const message = args.join(' ');
		if (message.includes('socket.io') ||
			message.includes('ERR_CONNECTION_TIMED_OUT') ||
			message.includes('Error connecting to socket.io')) {
			return; // Bu hataları gösterme
		}
		originalError.apply(console, args);
	};
})();

frappe.pages['hammadde-eksikleri-takip-sayfasi'].on_page_load = function(wrapper) {
	// Socket.io hatalarını görmezden gel - bu sayfa için gerekli değil
	if (window.io && window.io.socket) {
		try {
			window.io.socket.on('error', function() {
				// Socket.io hatalarını sessizce görmezden gel
			});
		} catch(e) {
			// Ignore
		}
	}

	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Hammadde Eksikleri Takip Sayfası',
		single_column: true
	});

	let report = new HammaddeEksikleriRaporu(page);
	$(wrapper).bind('show', function() {
		report.refresh();
	});
};

class HammaddeEksikleriRaporu {
	constructor(page) {
		this.page = page;
		this.filters = {};
		this.profileDataLoaded = false;
		this.loadingRequest = null;
		this.make();
	}

	make() {
		let me = this;

		this.container = $('<div class="hammadde-eksikleri-takip-sayfasi"></div>').appendTo(this.page.main);
		this.summaryContainer = $('<div class="row mb-3" id="summary-cards"></div>').appendTo(this.container);
		this.filterContainer = $('<div class="mb-3" id="filter-container"></div>').appendTo(this.container);
		this.tableContainer = $('<div class="table-responsive" id="table-container" style="max-height: calc(100vh - 350px); overflow-y: auto; overflow-x: auto; position: relative;"></div>').appendTo(this.container);
		this.profileContainer = $('<div class="mt-4" id="profile-container"></div>').appendTo(this.container);
		this.profileFilterContainer = $('<div class="mb-3" id="profile-filter-container"></div>').appendTo(this.profileContainer);

		this.setupFilters();

		$('#btn-refresh').on('click', function() {
			me.loadData();
		});

		$('#btn-create-mr-for-all').on('click', function() {
			me.createMaterialRequestForAll();
		});

		// Ana verileri yükle - profil verilerini lazy load yap
		this.loadData();

		// Profil verilerini sadece kullanıcı aşağı kaydırdığında yükle
		this.setupLazyLoadProfile();
	}

	setupFilters() {
		let me = this;

		let filterHtml = `
			<div class="card border-0 shadow-sm">
				<div class="card-body p-3">
					<div class="row align-items-end">
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057;">Hammadde Kodu</label>
							<input type="text" class="form-control form-control-sm" id="filter-item-code" placeholder="Hammadde kodu ile ara...">
						</div>
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057;">Hammadde Adı</label>
							<input type="text" class="form-control form-control-sm" id="filter-item-name" placeholder="Hammadde adı ile ara...">
						</div>
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057;">Ürün Grubu</label>
							<select class="form-control form-control-sm" id="filter-item-group">
								<option value="">Tümü</option>
							</select>
						</div>
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057; visibility: hidden;">İşlemler</label>
							<div class="d-flex justify-content-end">
								<button class="btn btn-outline-primary btn-sm mr-2" id="btn-refresh" style="min-width: 90px;">
									<i class="fa fa-refresh"></i> Yenile
								</button>
								<button class="btn btn-danger btn-sm" id="btn-create-mr-for-all" style="min-width: 280px;">
									<i class="fa fa-plus"></i> Eksik Hammaddeler için Satınalma Talebi Oluştur
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		this.filterContainer.html(filterHtml);

		$('#filter-item-code, #filter-item-name').on('keyup', function() {
			clearTimeout(me.filterTimeout);
			me.filterTimeout = setTimeout(function() {
				me.applyFilters();
			}, 300);
		});

		$('#filter-item-group').on('change', function() {
			me.applyFilters();
		});

		this.loadItemGroups();
	}

	loadItemGroups() {
		let me = this;
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Item Group',
				fields: ['name'],
				limit_page_length: 1000
			},
			callback: function(r) {
				if (r.message) {
					let select = $('#filter-item-group');
					r.message.forEach(function(group) {
						select.append(`<option value="${group.name}">${group.name}</option>`);
					});
				}
			}
		});
	}

	applyFilters() {
		let me = this;
		me.filters = {
			item_code: $('#filter-item-code').val() || null,
			item_name: $('#filter-item-name').val() || null,
			item_group: $('#filter-item-group').val() || null
		};
		Object.keys(me.filters).forEach(key => {
			if (!me.filters[key]) delete me.filters[key];
		});
		me.loadData();
	}

	loadData() {
		let me = this;

		if (this.loadingRequest) {
			// Eğer zaten bir istek varsa, önceki isteği iptal et
			if (this.loadingRequest.xhr && this.loadingRequest.xhr.abort) {
				this.loadingRequest.xhr.abort();
			}
		}

		this.showLoading();

		// Loading timeout - eğer 30 saniye içinde yanıt gelmezse kullanıcıyı bilgilendir
		let loadingTimeout = setTimeout(function() {
			if (me.loadingRequest) {
				me.tableContainer.html(`
					<div class="alert alert-warning" role="alert">
						<i class="fa fa-clock-o"></i> Veriler yükleniyor, lütfen bekleyin... (Bu işlem biraz zaman alabilir)
					</div>
				`);
			}
		}, 30000);

		this.loadingRequest = frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.hammadde_eksikleri_takip_sayfasi.hammadde_eksikleri_takip_sayfasi.get_all_shortages_report',
			args: {
				filters: me.filters
			},
			timeout: 60000, // 60 saniye timeout (sorgu optimize edildi, daha hızlı)
			callback: function(r) {
				clearTimeout(loadingTimeout);
				me.loadingRequest = null;
				if (r.message && r.message.success) {
					me.renderReport(r.message);
				} else {
					let errorMsg = r.message?.error || 'Veri yüklenirken hata oluştu';
					if (errorMsg.includes('timeout') || errorMsg.includes('Timeout') || errorMsg.includes('max_statement_time') || errorMsg.includes('interrupted')) {
						errorMsg = 'Sorgu çok uzun sürdü. Lütfen filtreleri daraltıp tekrar deneyin veya sistem yöneticisine başvurun.';
					}
					me.showError(errorMsg);
				}
			},
			error: function(err) {
				clearTimeout(loadingTimeout);
				me.loadingRequest = null;
				if (err.status !== 0) { // Abort edilmediyse hata göster
					let errorMsg = err.message || 'Bilinmeyen hata';
					if (err.status === 0 || errorMsg.includes('aborted')) {
						// İstek iptal edildi
						return;
					}
					if (errorMsg.includes('ERR_CONNECTION_TIMED_OUT') || errorMsg.includes('timeout') || errorMsg.includes('max_statement_time')) {
						errorMsg = 'Sorgu çok uzun sürdü. Lütfen filtreleri daraltıp tekrar deneyin veya sistem yöneticisine başvurun.';
					}
					me.showError('Sunucu hatası: ' + errorMsg);
				}
			}
		});
	}

	showLoading() {
		this.tableContainer.html(`
			<div class="text-center p-5">
				<div class="spinner-border text-primary" role="status">
					<span class="sr-only">Yükleniyor...</span>
				</div>
				<p class="mt-3 text-muted">Veriler yükleniyor...</p>
			</div>
		`);
		this.summaryContainer.html('');
	}

	showError(message) {
		this.tableContainer.html(`
			<div class="alert alert-danger" role="alert">
				<i class="fa fa-exclamation-triangle"></i> <strong>Hata:</strong> ${message}
				<div class="mt-2">
					<button class="btn btn-sm btn-primary" onclick="location.reload()">
						<i class="fa fa-refresh"></i> Sayfayı Yenile
					</button>
					<button class="btn btn-sm btn-secondary ml-2" id="btn-retry-load">
						<i class="fa fa-repeat"></i> Tekrar Dene
					</button>
				</div>
			</div>
		`);
		this.summaryContainer.html('');

		// Retry butonu
		let me = this;
		$('#btn-retry-load').off('click').on('click', function() {
			me.loadData();
		});
	}

	renderReport(data) {
		this.renderSummary(data.summary);
		this.renderTable(data.data);

		// Profil verilerini lazy load yap - sadece kullanıcı görüntülemek istediğinde yükle
		// this.profileDataLoaded = false;
		// this.setupProfileFilters();
	}

	renderSummary(summary) {
		let html = `
			<div class="col-auto mb-2">
				<div class="card border-danger" style="background-color: #fff5f5; min-width: 200px;">
					<div class="card-body py-2 px-3">
						<div class="text-center">
							<div class="text-muted mb-1" style="font-size: 0.85rem;">Toplam Eksik Kalem</div>
							<div class="text-danger font-weight-bold" style="font-size: 1.8rem;">${summary.total_items || 0}</div>
						</div>
					</div>
				</div>
			</div>
		`;
		this.summaryContainer.html(html);
	}

	renderTable(data) {
		let me = this;

		if (!data || data.length === 0) {
			this.tableContainer.html(`
				<div class="alert alert-info" role="alert">
					<i class="fa fa-info-circle"></i>
					Filtrelere uygun hammadde bulunamadı.
					<br><small class="text-muted">Not: Sadece siparişlerde kullanılan, rezervi olan veya eksik miktarı bulunan hammaddeler gösterilir.</small>
				</div>
			`);
			return;
		}

		let html = `
			<table class="table table-bordered table-hover table-sm" style="font-size: 0.85rem; border-collapse: separate; border-spacing: 0; width: 100%;">
				<thead style="position: sticky; top: 0; z-index: 1020;">
					<tr style="background-color: #dc3545;">
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; background-color: #dc3545; color: white; border-bottom: 2px solid #c82333; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Hammadde Kodu</th>
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; background-color: #dc3545; color: white; border-bottom: 2px solid #c82333; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Hammadde Adı</th>
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; background-color: #dc3545; color: white; border-bottom: 2px solid #c82333; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Fiziki Stok</th>
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; background-color: #dc3545; color: white; border-bottom: 2px solid #c82333; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Toplam Rezerv</th>
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; background-color: #dc3545; color: white; border-bottom: 2px solid #c82333; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Mevcut Talep</th>
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; background-color: #dc3545; color: white; border-bottom: 2px solid #c82333; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Satınalma Siparişi</th>
						<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; background-color: #c82333; color: white; border-bottom: 2px solid #a01e2a; box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.1);">Açık Miktar</th>
					</tr>
				</thead>
				<tbody>
		`;

		data.forEach((row, index) => {
			let shortage = row.shortage || 0;
			let shortageClass = shortage > 0 ? 'text-danger font-weight-bold' : 'text-success';

			html += `
				<tr style="background-color: ${index % 2 === 0 ? '#f9f9f9' : 'white'};">
					<td style="padding: 8px;">
						<a href="/app/item/${row.item_code}" target="_blank" style="color: #1976d2; font-weight: bold; text-decoration: underline;">
							${row.item_code || '-'}
						</a>
					</td>
					<td style="padding: 8px; font-weight: bold;">${row.item_name || '-'}</td>
					<td style="padding: 8px; text-align: right; background-color: #d4edda; cursor: pointer; font-weight: bold; color: #1976d2; text-decoration: underline;"
						class="warehouse-stock-link"
						data-item-code="${row.item_code}"
						data-item-name="${row.item_name || row.item_code}">
						${this.formatNumber(row.total_stock || 0)}
					</td>
					<td style="padding: 8px; text-align: right; background-color: #e2e3e5; cursor: pointer; font-weight: bold;"
						class="reserve-detail-link text-primary"
						data-item-code="${row.item_code}">
						${this.formatNumber(row.total_reserved || 0)}
					</td>
					<td style="padding: 8px; text-align: right; cursor: pointer; font-weight: bold; color: #1976d2; text-decoration: underline;"
						class="mr-detail-link"
						data-item-code="${row.item_code}">
						${this.formatNumber(row.pending_mr_qty || 0)}
					</td>
					<td style="padding: 8px; text-align: right; cursor: pointer; font-weight: bold; color: #1976d2; text-decoration: underline;"
						class="po-detail-link"
						data-item-code="${row.item_code}">
						${this.formatNumber(row.pending_po_qty || 0)}
					</td>
					<td style="padding: 8px; text-align: right; background-color: #ffcccc; font-weight: bold;" class="${shortageClass}">${this.formatNumber(shortage, 4)}</td>
				</tr>
			`;
		});

		html += `
				</tbody>
			</table>
		`;

		this.tableContainer.html(html);
		this.attachEventHandlers();
	}

	attachEventHandlers() {
		let me = this;

		$('.warehouse-stock-link').on('click', function() {
			let itemCode = $(this).data('item-code');
			let itemName = $(this).data('item-name');
			me.showWarehouseStockModal(itemCode, itemName);
		});

		$('.reserve-detail-link').on('click', function() {
			let itemCode = $(this).data('item-code');
			me.showReserveDetails(itemCode);
		});

		$('.mr-detail-link').on('click', function() {
			let itemCode = $(this).data('item-code');
			me.showMaterialRequestDetails(itemCode);
		});

		$('.po-detail-link').on('click', function() {
			let itemCode = $(this).data('item-code');
			me.showPurchaseOrderDetails(itemCode);
		});
	}

	showReserveDetails(itemCode) {
		let me = this;

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.hammadde_eksikleri_takip_sayfasi.hammadde_eksikleri_takip_sayfasi.get_reserve_details',
			args: { item_code: itemCode },
			callback: function(r) {
				if (r.message && r.message.success) {
					me.showDetailsModal('Rezerv Detayları', r.message.data, [
						'Satış Siparişi',
						'Miktar',
						'Müşteri',
						'Teslimat Tarihi',
						'Sipariş Tarihi'
					], 'sales-order');
				} else {
					frappe.show_alert({
						message: 'Rezerv detayları yüklenemedi',
						indicator: 'red'
					}, 3);
				}
			}
		});
	}

	showMaterialRequestDetails(itemCode) {
		let me = this;

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.hammadde_eksikleri_takip_sayfasi.hammadde_eksikleri_takip_sayfasi.get_material_request_details',
			args: { item_code: itemCode },
			callback: function(r) {
				if (r.message && r.message.success) {
					me.showDetailsModal('Malzeme Talep Detayları', r.message.data, [
						'Belge No',
						'Satış Siparişi',
						'Miktar',
						'Sipariş Edilen',
						'Tarih'
					], 'material-request');
				} else {
					frappe.show_alert({
						message: 'Malzeme talep detayları yüklenemedi',
						indicator: 'red'
					}, 3);
				}
			}
		});
	}

	showPurchaseOrderDetails(itemCode) {
		let me = this;

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.hammadde_eksikleri_takip_sayfasi.hammadde_eksikleri_takip_sayfasi.get_purchase_order_details',
			args: { item_code: itemCode },
			callback: function(r) {
				if (r.message && r.message.success) {
					me.showDetailsModal('Satınalma Siparişi Detayları', r.message.data, [
						'Belge No',
						'Tedarikçi',
						'Miktar',
						'Teslim Alınan',
						'Bekleyen',
						'Teslim Tarihi'
					], 'purchase-order');
				} else {
					frappe.show_alert({
						message: 'Satınalma siparişi detayları yüklenemedi',
						indicator: 'red'
					}, 3);
				}
			}
		});
	}

	showWarehouseStockModal(itemCode, itemName) {
		let me = this;

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.hammadde_eksikleri_takip_sayfasi.hammadde_eksikleri_takip_sayfasi.get_warehouse_stock_details',
			args: { item_code: itemCode },
			callback: function(r) {
				if (r.message && r.message.success && r.message.data.length > 0) {
					let html = `<div style="overflow-x:auto;">`;
					html += `<div class="mb-3"><strong>Ürün:</strong> ${itemCode} - ${itemName}</div>`;
					html += `<table class='table table-bordered table-sm table-hover'>`;
					html += `<thead style="background-color: #f8f9fa;"><tr>`;
					html += `<th style="padding: 10px; font-size: 0.85rem; font-weight: bold;">Depo</th>`;
					html += `<th style="padding: 10px; font-size: 0.85rem; font-weight: bold; text-align: right;">Stok Miktarı</th>`;
					html += `</tr></thead><tbody>`;

					let totalQty = 0;
					r.message.data.forEach(function(wh) {
						let qty = parseFloat(wh.qty || 0);
						totalQty += qty;
						html += `<tr>`;
						html += `<td style="padding: 8px; font-size: 0.85rem; font-weight: bold;">${wh.warehouse}</td>`;
						html += `<td style="padding: 8px; font-size: 0.85rem; text-align: right; font-weight: bold; color: #28a745;">${me.formatNumber(qty)}</td>`;
						html += `</tr>`;
					});

					html += `<tr style="background-color: #f8f9fa; font-weight: bold;">`;
					html += `<td style="padding: 8px; font-size: 0.85rem;">Toplam</td>`;
					html += `<td style="padding: 8px; font-size: 0.85rem; text-align: right; color: #28a745;">${me.formatNumber(totalQty)}</td>`;
					html += `</tr>`;
					html += `</tbody></table></div>`;

					frappe.msgprint({
						title: 'Depo Bazında Stok Detayları',
						indicator: 'green',
						message: html,
						wide: true
					});
				} else {
					frappe.show_alert({
						message: 'Depo bazında stok bilgisi bulunamadı',
						indicator: 'orange'
					}, 3);
				}
			},
			error: function(err) {
				frappe.show_alert({
					message: 'Stok detayları yüklenirken hata oluştu',
					indicator: 'red'
				}, 3);
			}
		});
	}

	showDetailsModal(title, details, columns, doctype) {
		if (!details || details.length === 0) {
			frappe.show_alert({
				message: 'Detay bulunamadı',
				indicator: 'orange'
			}, 3);
			return;
		}

		let html = `<div style='overflow-x:auto; max-height: 70vh;'>`;
		html += `<table class='table table-bordered table-sm table-hover'>`;
		html += `<thead style="background-color: #f8f9fa;"><tr>`;
		columns.forEach((col) => {
			html += `<th style="padding: 10px; font-size: 0.85rem; font-weight: bold;">${col}</th>`;
		});
		html += `</tr></thead><tbody>`;

		details.forEach((detail) => {
			html += `<tr>`;
			columns.forEach((col) => {
				let val = '';
				if (col === 'Belge No') {
					let docVal = detail.material_request || detail.purchase_order || '';
					if (docVal) {
						val = `<a href="/app/${doctype}/${docVal}" target="_blank" style="color: #1976d2; font-weight: bold; text-decoration: underline;">${docVal}</a>`;
					} else {
						val = '-';
					}
				} else if (col === 'Satış Siparişi') {
					let docVal = detail.sales_order || '';
					if (docVal) {
						val = `<a href="/app/sales-order/${docVal}" target="_blank" style="color: #1976d2; font-weight: bold; text-decoration: underline;">${docVal}</a>`;
					} else {
						val = '-';
					}
				} else if (col === 'Miktar') {
					val = this.formatNumber(detail.qty || detail.quantity || 0);
				} else if (col === 'Sipariş Edilen') {
					val = this.formatNumber(detail.ordered_qty || 0);
				} else if (col === 'Teslim Alınan') {
					val = this.formatNumber(detail.received_qty || 0);
				} else if (col === 'Bekleyen') {
					val = this.formatNumber(detail.pending_qty || 0);
				} else if (col === 'Tarih' || col === 'Sipariş Tarihi') {
					val = detail.transaction_date || '-';
				} else if (col === 'Teslimat Tarihi' || col === 'Teslim Tarihi') {
					val = detail.delivery_date || detail.schedule_date || '-';
				} else if (col === 'Müşteri') {
					val = detail.customer || '-';
				} else if (col === 'Tedarikçi') {
					val = detail.supplier || '-';
				} else {
					val = detail[col.toLowerCase().replace(/ /g, '_')] || detail[col] || '-';
				}
				html += `<td style="padding: 8px; font-size: 0.85rem;">${val}</td>`;
			});
			html += `</tr>`;
		});

		html += `</tbody></table></div>`;

		frappe.msgprint({
			title: title,
			indicator: 'blue',
			message: html,
			wide: true
		});
	}

	formatNumber(value, decimals = 3) {
		if (value === null || value === undefined) return '0,' + '0'.repeat(decimals);
		let num = parseFloat(value);
		if (isNaN(num)) return '0,' + '0'.repeat(decimals);

		if (num > 0 && num < 0.01) {
			decimals = Math.max(decimals, 4);
		}

		let formatted = num.toFixed(decimals);
		let parts = formatted.split('.');
		let integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
		let decimalPart = parts[1] || '';

		return integerPart + (decimalPart ? ',' + decimalPart : '');
	}

	createMaterialRequestForAll() {
		let me = this;

		frappe.confirm(
			'Tüm siparişlere ait eksikler için satınalma talebi oluşturulacak. Devam etmek istiyor musunuz?',
			function() {
				frappe.call({
					method: 'uretim_planlama.sales_order_hooks.raw_materials.create_material_request_for_all_shortages',
					freeze: true,
					freeze_message: 'Satınalma talebi oluşturuluyor...',
					callback: function(r) {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: r.message.message,
								indicator: 'green'
							}, 5);

							setTimeout(function() {
								me.loadData();
							}, 1000);

							if (r.message.mr_name) {
								setTimeout(function() {
									frappe.set_route('Form', 'Material Request', r.message.mr_name);
								}, 2000);
							}
						} else {
							frappe.show_alert({
								message: r.message?.message || 'Hata oluştu',
								indicator: 'red'
							}, 5);
						}
					},
					error: function(err) {
						frappe.show_alert({
							message: 'Sunucu hatası: ' + (err.message || 'Bilinmeyen hata'),
							indicator: 'red'
						}, 5);
					}
				});
			},
			function() {}
		);
	}

	loadProfileLengthData() {
		let me = this;

		let profileFilters = {};
		if ($('#profile-filter-item-code').length) {
			profileFilters.profile_item_code = $('#profile-filter-item-code').val() || null;
		}
		if ($('#profile-filter-item-group').length) {
			profileFilters.profile_item_group = $('#profile-filter-item-group').val() || null;
		}
		if ($('#profile-filter-length').length) {
			profileFilters.profile_length = $('#profile-filter-length').val() || null;
		}

		Object.keys(profileFilters).forEach(key => {
			if (!profileFilters[key]) delete profileFilters[key];
		});

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.hammadde_eksikleri_takip_sayfasi.hammadde_eksikleri_takip_sayfasi.get_profile_length_shortages',
			args: {
				filters: profileFilters
			},
			callback: function(r) {
				if (r.message && r.message.success && r.message.data && r.message.data.length > 0) {
					me.renderProfileLengthTable(r.message.data);
				} else {
					if (!me.profileContainer.find('#profile-table-container').length) {
						me.profileContainer.append('<div id="profile-table-container"></div>');
					}
					if (r.message && r.message.error) {
						me.profileContainer.find('#profile-table-container').html('<div style="padding: 10px; color: red;">Hata: ' + r.message.error + '</div>');
					} else {
						me.profileContainer.find('#profile-table-container').html('<div style="padding: 10px; color: #888;">Profil boy verisi bulunamadı.</div>');
					}
				}
			},
			error: function(err) {
				if (!me.profileContainer.find('#profile-table-container').length) {
					me.profileContainer.append('<div id="profile-table-container"></div>');
				}
				me.profileContainer.find('#profile-table-container').html('<div style="padding: 10px; color: red;">Profil boy verisi yüklenirken hata oluştu: ' + (err.message || 'Bilinmeyen hata') + '</div>');
			}
		});
	}

	renderProfileLengthTable(data) {
		let me = this;

		if (!data || data.length === 0) {
			if (!this.profileContainer.find('#profile-table-container').length) {
				this.profileContainer.append('<div id="profile-table-container"></div>');
			}
			this.profileContainer.find('#profile-table-container').html('<div style="padding: 10px; color: #888;">Profil boy verisi bulunamadı.</div>');
			return;
		}

		let rows = data.sort((a, b) => {
			if (a.item_code !== b.item_code) {
				return a.item_code.localeCompare(b.item_code);
			}
			return (a.length || 0) - (b.length || 0);
		});

		let html = `
			<div class="card mt-3">
				<div class="card-header bg-info text-white" style="cursor: pointer;" id="profile-header">
					<h6 class="mb-0">
						<i class="fa fa-chevron-down"></i> Profil Boy Bazında Stok Durumu
					</h6>
				</div>
				<div class="card-body p-0" id="profile-body">
					<div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
						<table class="table table-bordered table-hover table-sm mb-0" style="font-size: 0.85rem;">
							<thead style="background-color: #17a2b8; color: white; position: sticky; top: 0; z-index: 100;">
								<tr>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; position: sticky; top: 0; background-color: #17a2b8;">Ürün Kodu</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; position: sticky; top: 0; background-color: #17a2b8;">Ürün Grubu</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; position: sticky; top: 0; background-color: #17a2b8;">Boy (m)</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; position: sticky; top: 0; background-color: #17a2b8;">Stok Miktarı</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; position: sticky; top: 0; background-color: #17a2b8;">Toplam (mtül)</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; position: sticky; top: 0; background-color: #17a2b8;">Minimum Stok Miktarı</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: right; position: sticky; top: 0; background-color: #17a2b8;">Yeniden Sipariş Miktarı</th>
									<th style="padding: 10px; font-size: 0.8rem; font-weight: bold; text-align: center; position: sticky; top: 0; background-color: #17a2b8;">Parça Profil mi?</th>
								</tr>
							</thead>
							<tbody>
		`;

		rows.forEach((row, index) => {
			html += `
				<tr style="background-color: ${index % 2 === 0 ? '#f9f9f9' : 'white'};">
					<td style="padding: 8px; font-weight: bold;">${row.item_code || '-'}</td>
					<td style="padding: 8px;">${row.item_group || '-'}</td>
					<td style="padding: 8px; text-align: right; font-weight: bold;">${this.formatNumber(row.length || 0, 1)}</td>
					<td style="padding: 8px; text-align: right; font-weight: bold;">${this.formatNumber(row.stock_qty || 0, 1)}</td>
					<td style="padding: 8px; text-align: right; font-weight: bold;">${this.formatNumber(row.total_length || 0, 1)}</td>
					<td style="padding: 8px; text-align: right; font-weight: bold;">${this.formatNumber(row.min_qty || 0, 1)}</td>
					<td style="padding: 8px; text-align: right; font-weight: bold;">${this.formatNumber(row.reorder_qty || 0, 1)}</td>
					<td style="padding: 8px; text-align: center;">
						<input type="checkbox" ${row.is_scrap_piece ? 'checked' : ''} disabled>
					</td>
				</tr>
			`;
		});

		html += `
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`;

		if (!this.profileContainer.find('#profile-table-container').length) {
			this.profileContainer.append('<div id="profile-table-container"></div>');
		}
		this.profileContainer.find('#profile-table-container').html(html);

		$('#profile-header').off('click').on('click', function() {
			$('#profile-body').slideToggle();
			let icon = $(this).find('i');
			icon.toggleClass('fa-chevron-down fa-chevron-up');
		});
	}

	setupProfileFilters() {
		let me = this;

		if (this.profileFilterContainer.html()) {
			return;
		}

		let filterHtml = `
			<div class="card border-0 shadow-sm">
				<div class="card-body p-3">
					<div class="row align-items-end">
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057;">Ürün Kodu</label>
							<input type="text" class="form-control form-control-sm" id="profile-filter-item-code" placeholder="Ürün kodu ile ara...">
						</div>
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057;">Ürün Grubu</label>
							<select class="form-control form-control-sm" id="profile-filter-item-group">
								<option value="">Tümü</option>
							</select>
						</div>
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057;">Boy (m)</label>
							<input type="text" class="form-control form-control-sm" id="profile-filter-length" placeholder="Boy değeri...">
						</div>
						<div class="col-md-3">
							<label class="form-label mb-1" style="font-size: 0.875rem; font-weight: 500; color: #495057; visibility: hidden;">İşlemler</label>
							<div class="d-flex justify-content-end">
								<button class="btn btn-outline-primary btn-sm" id="profile-btn-refresh" style="min-width: 90px;">
									<i class="fa fa-refresh"></i> Yenile
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		this.profileFilterContainer.html(filterHtml);

		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Item Group',
				fields: ['name'],
				limit_page_length: 1000
			},
			callback: function(r) {
				if (r.message) {
					let select = $('#profile-filter-item-group');
					r.message.forEach(function(group) {
						select.append(`<option value="${group.name}">${group.name}</option>`);
					});
					if (!me.profileDataLoaded) {
						me.loadProfileLengthData();
						me.profileDataLoaded = true;
					}
				}
			}
		});

		$('#profile-filter-item-code, #profile-filter-length').on('keyup', function() {
			clearTimeout(me.profileFilterTimeout);
			me.profileFilterTimeout = setTimeout(function() {
				me.loadProfileLengthData();
			}, 300);
		});

		$('#profile-filter-item-group').on('change', function() {
			me.loadProfileLengthData();
		});

		$('#profile-btn-refresh').on('click', function() {
			me.loadProfileLengthData();
		});
	}

	setupLazyLoadProfile() {
		let me = this;

		// Profil bölümüne bir buton ekle - kullanıcı tıklayınca yükle
		if (!this.profileContainer.find('#profile-load-trigger').length) {
			let triggerHtml = `
				<div class="card border-info mt-3" id="profile-load-trigger">
					<div class="card-body text-center p-4" style="cursor: pointer;">
						<h6 class="mb-2">
							<i class="fa fa-info-circle"></i> Profil Boy Bazında Stok Durumu
						</h6>
						<p class="text-muted mb-0" style="font-size: 0.9rem;">
							Profil stok verilerini görüntülemek için tıklayın
						</p>
					</div>
				</div>
			`;
			this.profileContainer.append(triggerHtml);

			$('#profile-load-trigger').on('click', function() {
				$(this).remove();
				me.profileDataLoaded = false;
				me.setupProfileFilters();
			});
		}
	}

	refresh() {
		this.loadData();
	}
}
