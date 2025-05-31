frappe.pages['operasyon_plani'].on_page_load = function(wrapper) {
	frappe.require(['/assets/uretim_planlama/js/status_colors.js'], function() {
		if (!uretim_planlama?.status_colors) {
			frappe.msgprint({
				title: 'Hata',
				message: 'Durum renkleri yüklenemedi. Lütfen sayfayı yenileyin.',
				indicator: 'red'
			});
			return;
		}
		initializePage(wrapper);
	});
};

function initializePage(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'İş İstasyonu - Operasyon Planı',
		single_column: true
	});

	var cache = {};
	let content = $('<div></div>');
	$(page.body).append(content);

	let currentDate = getMonday(new Date());
	const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
	const weekdays = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];

	// Header oluştur
	const headerRow = $(`
		<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
			<div style="display: flex; gap: 8px; align-items: center;">
				<button id="prev_btn" class="btn btn-default btn-sm" style="padding: 2px 8px;">&lt;</button>
				<span id="current_label" style="font-weight: bold; margin: 0 10px;"></span>
				<button id="next_btn" class="btn btn-default btn-sm" style="padding: 2px 8px;">&gt;</button>
				<button id="today_btn" class="btn btn-primary btn-sm" style="margin-left: 12px; padding: 2px 12px; font-size: 13px;">Bu Hafta</button>
			</div>
			<div id="filter_bar" style="display: flex; gap: 10px; align-items: center;">
				<select id="workstation_filter" class="form-control" style="width: 140px; font-size: 13px;">
					<option value="">Tüm İstasyonlar</option>
				</select>
				<select id="operation_filter" class="form-control" style="width: 140px; font-size: 13px;">
					<option value="">Tüm Operasyonlar</option>
				</select>
			</div>
		</div>
	`);
	$(page.body).prepend(headerRow);

	const tableContainer = $('<div id="schedule_tables"></div>');
	content.append(tableContainer);

	// Yardımcı fonksiyonlar
	function getMonday(d) {
		d = new Date(d);
		// UTC'ye göre pazartesi gününü bul
		const day = d.getUTCDay();
		const diff = d.getUTCDate() - day + (day === 0 ? -6 : 1);
		return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), diff));
	}

	function updateLabel(days) {
		if (!days?.length) return;
		const label = $('#current_label');
		// UTC tarihlerini kullan
		const start = new Date(days[0].date + 'T00:00:00Z');
		const end = new Date(days[days.length - 1].date + 'T00:00:00Z');
		const format = d => `${String(d.getUTCDate()).padStart(2,'0')} ${months[d.getUTCMonth()]}`;
		label.text(`${format(start)} - ${format(end)}`);
	}

	function load_schedule_dynamic() {
		let start = getMonday(currentDate);
		let end = new Date(start);
		end.setUTCDate(start.getUTCDate() + 6);

		let week_start = start.toISOString().split('T')[0];
		let week_end = end.toISOString().split('T')[0];

		if (cache[week_start]) {
			render_tables(cache[week_start]);
			updateLabel(cache[week_start].days);
			return;
		}

		$('#schedule_tables').html('<div style="text-align:center; color:#888; padding:40px;">Yükleniyor...</div>');

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.api.get_weekly_production_schedule',
			args: {
				week_start,
				week_end,
				workstation: $('#workstation_filter').val(),
				operation: $('#operation_filter').val(),
			},
			callback: function(r) {
				if (r.message) {
					// Tarihleri UTC olarak işle
					r.message.days = r.message.days.map(day => ({
						...day,
						date: new Date(day.date + 'T00:00:00Z').toISOString().split('T')[0]
					}));
					cache[week_start] = r.message;
					render_tables(r.message);
					updateLabel(r.message.days);
				} else {
					$('#schedule_tables').html('<div style="text-align:center; color:#888; padding:40px;">Kayıt bulunamadı.</div>');
				}
			},
			error: function() {
				$('#schedule_tables').html('<div style="text-align:center; color:#f44336; padding:40px;">Veri yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.</div>');
			}
		});
	}

	function render_tables(data) {
		const container = $('#schedule_tables');
		container.empty();

		const days = data.days || [];
		const active = data.workstations || [];

		active.forEach(ws => {
			const wrapper = $('<div style="margin-bottom: 30px;"></div>');
			// İş istasyonu ve operasyon adını doğru göster
			const workstationName = ws.name || '-';
			let operationName = '-';
			if (ws.operations && ws.operations.length === 1) {
				operationName = ws.operations[0];
			} else if (ws.operations && ws.operations.length > 1) {
				operationName = ws.operations.join(', ');
			}
			// Sarı kutu (infoBox)
			const infoBox = $(`
				<div style="margin-bottom: 8px; display: flex; justify-content: flex-start;">
					<div style="background: linear-gradient(90deg, #fffde4 0%, #ffe680 100%); border-radius: 10px; padding: 10px 28px; display: flex; flex-direction: row; align-items: center; box-shadow: 0 2px 8px #ffe68044; border: 1px solid #ffe680;">
						<span style='font-size:13px; color:#888; margin-right:8px; font-weight:bold;'>İş İstasyonu:</span>
						<span style='font-size:15px; color:#c62828; font-style:italic; font-weight:bold; margin-right:18px;'>${workstationName}</span>
						<span style='font-size:13px; color:#888; margin-right:8px; font-weight:bold;'>Operasyon:</span>
						<span style='font-size:15px; color:#c62828; font-style:italic; font-weight:bold;'>${operationName}</span>
					</div>
				</div>
			`);
			wrapper.append(infoBox);
			const header = $('<div style="display: flex; background-color: #003366; color: white; text-align: center;"></div>');
			days.forEach(d => {
				let bgColor = d.isHoliday ? 'linear-gradient(90deg, #fbc2eb 0%, #f9d1d1 100%)' : (d.isWeekend ? '#f5f5f5' : 'linear-gradient(90deg, #e3f2fd 0%, #90caf9 100%)');
				let textColor = d.isHoliday ? '#c62828' : (d.isWeekend ? '#616161' : '#1565c0');
				let label = `${d.weekday} ${String(new Date(d.date).getDate()).padStart(2, '0')}.${String(new Date(d.date).getMonth() + 1).padStart(2, '0')}`;
				header.append(`
					<div style="width: 14.2857%; padding: 10px; font-weight: bold; background: ${bgColor}; color: ${textColor}; border-right: 1px solid #fff;">
						${label}
					</div>`);
			});
			wrapper.append(header);

			const body = $('<div style="display: flex;"></div>');
			days.forEach(d => {
				// Silinen iş kartlarını filtrele
				const jobs = (ws.schedule?.[d.weekday] || []).filter(job => 
					job && typeof job === 'object' && job.name
				);
				const column = $('<div style="width: 14.2857%; padding: 6px 2px; min-height: 80px; border-right: 1px solid #eee; display: flex; flex-direction: column; align-items: stretch;"></div>');
				
				if (d.isHoliday && d.holidayReason && !(d.isWeekend && d.holidayReason === d.weekday)) {
					column.append(`<div style="font-size: 11px; color: #721c24; margin-bottom: 6px; text-align: center;">${d.holidayReason}</div>`);
				}

				jobs.forEach(job => {
					const badge = uretim_planlama.status_colors.getStatusBadge(job.status || 'Cancelled');
					// Modern job card kutusu
					const jobCard = $(`
						<div class="job-card"
							data-id="${job.name || ''}"
							data-work_order="${job.work_order || ''}"
							data-sales_order="${job.sales_order || ''}"
							data-status="${job.status || 'Cancelled'}"
							data-item_name="${job.item_name || ''}"
							data-item_code="${job.production_item || job.item_code || ''}"
							data-bom_no="${job.bom_no || ''}"
							data-for_quantity="${job.qty_to_manufacture ?? '-'}"
							data-total_completed_qty="${job.total_completed_qty ?? '-'}"
							data-start_time="${job.start_time || ''}"
							data-end_time="${job.end_time || ''}"
							data-actual_start_date="${job.actual_start || ''}"
							data-actual_end_date="${job.actual_end || ''}"
							data-total_time_in_mins="${job.duration ?? '-'}"
							data-operation="${job.operation || '-'}"
							style="background: linear-gradient(90deg, #a18cd1 0%, #fbc2eb 100%); color: #4a148c; margin-bottom: 3px; padding: 3px 6px; border-radius: 5px; font-size: 11px; min-height: 18px; display: flex; flex-direction: column; align-items: flex-start; box-shadow: 0 1px 4px 0 rgba(161,140,209,0.08); position:relative; cursor:pointer;">
							<div style="font-weight: 700; font-size: 12px; margin-bottom:1px; line-height:1.1;">${job.name}</div>
							<div style="font-size:10px; color:#555; font-weight:bold; margin-bottom:1px; line-height:1.1;">${job.item_name || ''}</div>
							<span style="position:absolute; bottom:4px; right:6px; padding:1px 7px; border-radius:10px; font-size:10px; font-weight:600; background:${badge.bg}; color:${badge.color}; box-shadow:0 1px 3px rgba(0,0,0,0.1);">${badge.label}</span>
						</div>
					`);
					// Modern hover tooltip
					jobCard.on('mouseenter', function(e) {
						// Tarih formatlama fonksiyonu
						function formatDate(val) {
							if (!val || val === '-') return '-';
							const d = new Date(val);
							if (isNaN(d.getTime())) return val;
							return `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth()+1).toString().padStart(2, '0')}.${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
						}
						// Planlanan tarih aralığı
						let planStart = formatDate(job.start_time);
						let planEnd = formatDate(job.end_time);
						let planRange = (planStart && planEnd && planStart !== planEnd) ? `${planStart} - ${planEnd}` : planStart;
						// Üretilen miktar
						let producedQty = (job.total_completed_qty !== undefined && job.total_completed_qty !== null && job.total_completed_qty !== '') ? job.total_completed_qty : (job.completed_qty !== undefined ? job.completed_qty : '-');
						let forQuantity = (job.for_quantity !== undefined && job.for_quantity !== null) ? job.for_quantity : (job.qty_to_manufacture !== undefined ? job.qty_to_manufacture : '-');
						const tooltipHtml = `
							<div style="background:#fff; border-radius:10px; box-shadow:0 4px 16px rgba(0,0,0,0.13); padding:14px 18px; min-width:260px; max-width:340px; font-size:14px; color:#222;">
								<div style="font-size:16px; font-weight:700; color:#1976d2; margin-bottom:6px;">${job.name}</div>
								<div style='margin-bottom:4px;'><span style='color:#888;'>Operasyon:</span> <span style='font-weight:600;'>${job.operation || '-'}</span></div>
								${job.sales_order ? `<div style='margin-bottom:4px;'><span style='color:#888;'>Sipariş No:</span> <span style='font-weight:600;'>${job.sales_order}</span></div>` : ''}
								<div style='margin-bottom:4px;'><span style='color:#888;'>Ürün:</span> <span style='font-weight:600;'>${job.item_name || '-'}</span></div>
								${job.customer ? `<div style='margin-bottom:4px;'><span style='color:#888;'>Bayi:</span> <span style='font-weight:600;'>${job.customer}</span></div>` : ''}
								${job.custom_end_customer ? `<div style='margin-bottom:4px;'><span style='color:#888;'>Müşteri:</span> <span style='font-weight:600;'>${job.custom_end_customer}</span></div>` : ''}
								<div style='margin-bottom:4px; font-size:14px; display:flex; flex-direction:column; gap:2px;'>
									<div style='display:flex;'><span style='color:#888; min-width:110px;'>Planlanan Baş:</span><span>${planStart}</span></div>
									<div style='display:flex;'><span style='color:#888; min-width:110px;'>Planlanan Bit:</span><span>${planEnd}</span></div>
								</div>
								<div style='margin-bottom:4px;'><span style='color:#888;'>Durum:</span> <span style="background:${badge.bg}; color:${badge.color}; border-radius:7px; font-size:14px; font-weight:600; padding:2px 10px; display:inline-block;">${badge.label}</span></div>
								</div>
						`;
						let tip = document.createElement('div');
						tip.className = 'fc-custom-tooltip';
						tip.innerHTML = tooltipHtml;
						tip.style.position = 'fixed';
						tip.style.zIndex = 9999;
						tip.style.pointerEvents = 'none';
						tip.style.left = (e.clientX + 16) + 'px';
						tip.style.top = (e.clientY + 8) + 'px';
						document.body.appendChild(tip);
						$(this).on('mousemove.tooltip', function(ev) {
							tip.style.left = (ev.clientX + 16) + 'px';
							tip.style.top = (ev.clientY + 8) + 'px';
						});
						$(this).on('mouseleave.tooltip', function() {
							if (tip && tip.parentNode) tip.parentNode.removeChild(tip);
							$(this).off('mousemove.tooltip mouseleave.tooltip');
						});
					});
					column.append(jobCard);
				});
				body.append(column);
			});
			wrapper.append(body);

			const footer = $('<div style="display: flex; border-top: 2px solid #bbb; background: #f8f9fa; font-size: 13px; font-weight: 500;"></div>');
			days.forEach((d, i) => {
				const info = ws.daily_info ? ws.daily_info[d.weekday] : null;
				let workMinutes = info ? info.work_minutes : 0;
				
				// Silinen iş kartlarını hariç tutarak planlanan dakikaları hesapla
				let plannedMinutes = 0;
				const validJobs = (ws.schedule?.[d.weekday] || []).filter(job => 
					job && typeof job === 'object' && job.name && job.duration
				);
				validJobs.forEach(job => {
					if (job.duration && typeof job.duration === 'number') {
						plannedMinutes += job.duration;
					}
				});

				let plannedHours = Math.floor(plannedMinutes / 60);
				let plannedMins = plannedMinutes % 60;
				
				// Doluluk oranını geçerli iş kartlarına göre hesapla
				let doluluk = workMinutes > 0 ? Math.round((plannedMinutes / workMinutes) * 100) : 0;
				doluluk = Math.min(doluluk, 100); // %100'ü geçmemesi için

				let barColor = doluluk < 60 ? 'linear-gradient(90deg, #43e97b 0%, #38f9d7 100%)' : 
							  (doluluk < 90 ? 'linear-gradient(90deg, #f9d423 0%, #ff4e50 100%)' : 
							  'linear-gradient(90deg, #ff5858 0%, #f09819 100%)');
				let textColor = doluluk < 60 ? '#219150' : (doluluk < 90 ? '#b8860b' : '#c62828');
				
				const isHoliday = d.isHoliday;
				let workHourStr = (!isHoliday && workMinutes > 0)
					? `<span style='color:#2196f3;'>${Math.floor(workMinutes/60)}sa ${workMinutes%60}dk</span>`
					: '-';
				let plannedStr = (!isHoliday && plannedMinutes > 0)
					? `<span style='color:#1976d2;'>${plannedHours}sa ${plannedMins}dk</span>`
					: '-';
				let dolulukStr = (!isHoliday && workMinutes > 0)
					? `<span style='color:${textColor}; font-weight:700;'>${doluluk}%</span>`
					: '-';

				footer.append(`
					<div style="width: 14.2857%; padding: 6px 2px; text-align: center;">
						<div style="margin-bottom:2px; color:#888; font-size:12px;">Çalışma: <b>${workHourStr}</b></div>
						<div style="margin-bottom:2px; color:#888; font-size:12px;">Planlanan: <b>${plannedStr}</b></div>
						<div style="margin-bottom:2px; color:#888; font-size:12px;">Doluluk: <b>${dolulukStr}</b></div>
						<div style="height: 8px; width: 80%; margin: 0 auto; background: #eee; border-radius: 4px; overflow: hidden;">
							<div style="width: ${Math.min(doluluk,100)}%; height: 100%; background: ${barColor}; transition: width 0.5s;"></div>
						</div>
					</div>
				`);
			});
			wrapper.append(footer);

			container.append(wrapper);
		});

		// Performans iyileştirmesi: job-card tıklama olayını delegate (on) ile bağlayıp, her render'da tekrarlı event eklemeyi önleyeceğim.
		// (Önceki kodda her render'da tüm job-card'lara ayrı ayrı click eventi ekleniyordu.)
		container.off('click', '.job-card').on('click', '.job-card', function () {
			const jobId = $(this).data('id') || '-';
			if (jobId === '-') return;
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.get_job_card_detail',
				args: { job_card_id: jobId },
				callback: function(r) {
					if (!r.message) return;
					const job = r.message;
					const badge = uretim_planlama.status_colors.getStatusBadge(job.status);
					let producedQty = (job.total_completed_qty !== undefined && job.total_completed_qty !== null && job.total_completed_qty !== '') ? job.total_completed_qty : (job.completed_qty !== undefined ? job.completed_qty : '-');
					let forQuantity = (job.for_quantity !== undefined && job.for_quantity !== null) ? job.for_quantity : (job.qty_to_manufacture !== undefined ? job.qty_to_manufacture : '-');
					function formatDate(val) {
						if (!val || val === '-') return "-";
						const d = new Date(val);
						if (isNaN(d.getTime())) return val;
						return `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth()+1).toString().padStart(2, '0')}.${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
					}
					let html = `<div style="margin-bottom:12px;">
						<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">İş Kartı</label><br>
							<a href="/app/job-card/${job.name}" target="_blank" style="font-weight:bold; color:#1976d2; text-decoration:underline;">${job.name}</a>
						</div>`;
					if (job.work_order && job.work_order !== '-') {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">İş Emri</label><br>
							<a href="/app/work-order/${job.work_order}" target="_blank" style="font-weight:bold; color:#388e3c; text-decoration:underline;">${job.work_order}</a>
						</div>`;
					}
					if (job.sales_order && job.sales_order !== '-') {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Satış Siparişi</label><br>
							<a href="/app/sales-order/${job.sales_order}" target="_blank" style="font-weight:bold; color:#f57c00; text-decoration:underline;">${job.sales_order}</a>
						</div>`;
					}
					if (job.production_item) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Ürün Adı</label><br>
							<a href="/app/item/${job.production_item}" target="_blank" style="font-weight:bold; color:#009688; text-decoration:underline;">${job.item_name}</a>
						</div>`;
					} else {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Ürün Adı</label><br>
							<span>${job.item_name}</span>
						</div>`;
					}
					if (job.bom_no) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">BOM Numarası</label><br>
							<a href="/app/bom/${job.bom_no}" target="_blank" style="font-weight:bold; color:#6d4c41; text-decoration:underline;">${job.bom_no}</a>
						</div>`;
					} else {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">BOM Numarası</label><br>
							<span>-</span>
						</div>`;
					}
					if (job.customer) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Bayi</label><br>
							<span style="font-weight:bold; color:#f70404">${job.customer}</span>
						</div>`;
					}
					if (job.custom_end_customer) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Müşteri</label><br>
							<span style="font-weight:bold; color:#10fb07">${job.custom_end_customer}</span>
						</div>`;
					}
					html += `<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Operasyon</label><br>
						<span style="font-weight:bold;">${job.operation}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Durumu</label><br>
						<span style="display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background:${badge.bg}; color:${badge.color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">${badge.label}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Üretilecek Miktar</label><br>
						<span>${forQuantity}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Üretilen Miktar</label><br>
						<span>${producedQty}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Planlanan Başlangıç</label><br>
						<span>${formatDate(job.expected_start_date)}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Planlanan Bitiş</label><br>
						<span>${formatDate(job.expected_end_date)}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Gerekli Beklenen Süre (dk)</label><br>
						<span>${job.time_required !== undefined ? job.time_required : '-'}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Fiili Başlangıç Tarihi</label><br>
						<span>${formatDate(job.actual_start_date)}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Fiili Bitiş Tarihi</label><br>
						<span>${formatDate(job.actual_end_date)}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Toplam Fiili Süre (dk)</label><br>
						<span>${job.total_time_in_mins !== undefined ? job.total_time_in_mins : '-'}</span>
					</div>
					</div>`;
					try {
						const dialog = new frappe.ui.Dialog({
							title: 'İş Kartı Detayı',
							size: 'large',
							fields: [
								{
									fieldtype: 'HTML',
									fieldname: 'job_card_detail_html',
									options: html
								}
							],
							primary_action_label: 'Kapat',
							primary_action() {
								dialog.hide();
							}
						});
						dialog.show();
					} catch (error) {
						frappe.msgprint({
							title: 'Hata',
							message: 'Detay görüntülenirken bir hata oluştu. Lütfen sayfayı yenileyip tekrar deneyin.',
							indicator: 'red'
						});
					}
				}
			});
		});
	}

	function showWorkOrderDetails(job) {
		const badge = uretim_planlama.status_colors.getStatusBadge(job.status);
		// ... rest of the details code ...
	}

	// Event handlers
	$('#today_btn').on('click', () => {
		currentDate = getMonday(new Date());
		load_schedule_dynamic();
	});

	$('#prev_btn').on('click', () => {
		currentDate.setDate(currentDate.getDate() - 7);
		load_schedule_dynamic();
	});

	$('#next_btn').on('click', () => {
		currentDate.setDate(currentDate.getDate() + 7);
		load_schedule_dynamic();
	});

	// Filtreleri yükle
	frappe.call({
		method: 'frappe.client.get_list',
		args: { doctype: 'Workstation', fields: ['name'] },
		callback: function(r) {
			if (r.message) {
				const wsFilter = $('#workstation_filter');
				wsFilter.empty().append('<option value="">Tüm İstasyonlar</option>');
				r.message.forEach(ws => {
					wsFilter.append(`<option value="${ws.name}">${ws.name}</option>`);
				});
			}
		}
	});

	frappe.call({
		method: 'frappe.client.get_list',
		args: { doctype: 'Operation', fields: ['name'] },
		callback: function(r) {
			if (r.message) {
				const opFilter = $('#operation_filter');
				opFilter.empty().append('<option value="">Tüm Operasyonlar</option>');
				r.message.forEach(op => {
					opFilter.append(`<option value="${op.name}">${op.name}</option>`);
				});
			}
		}
	});

	$('#workstation_filter, #operation_filter').on('change', function() {
		cache = {};
		load_schedule_dynamic();
	});

	// İlk yükleme
	load_schedule_dynamic();
}
