// Statü etiketleri global scope (ERPNext v15 iş emri statüleri, Türkçe ve renkli, dublicate yok)
const statusBadges = {
	'Not Started': { bg: '#ffd600', color: '#333', label: 'Açık' },
	'Completed':   { bg: '#43e97b', color: '#fff', label: 'Tamamlandı' },
	'Draft':       { bg: '#bdbdbd', color: '#fff', label: 'Taslak' }
};

// Operasyonlar için özel badge haritası (sadece 3 statü ve 3 renk)
const operationStatusBadges = {
	'Pending':      { bg: '#ffd600', color: '#333', label: 'Açık' },
	'Not Started':  { bg: '#ffd600', color: '#333', label: 'Açık' },
	'In Progress':  { bg: '#ff9800', color: '#fff', label: 'Devam Ediyor' },
	'In Process':   { bg: '#ff9800', color: '#fff', label: 'Devam Ediyor' },
	'Completed':    { bg: '#43e97b', color: '#fff', label: 'Tamamlandı' }
};

frappe.pages['is_emirleri_plani'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'İş Emirleri Planı',
		single_column: true
	});

	let content = $('<div></div>');
	$(page.body).append(content);

	let currentDate = getMonday(new Date());

	const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
	const weekdays = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];

	const headerRow = $(`
		<div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 12px; gap: 12px;">
			<button id="prev_btn" class="btn btn-default btn-sm" style="padding: 2px 8px;">&lt;</button>
			<span id="current_label" style="font-weight: bold; margin: 0 10px;"></span>
			<button id="next_btn" class="btn btn-default btn-sm" style="padding: 2px 8px;">&gt;</button>
			<button id="today_btn" class="btn btn-primary btn-sm" style="margin-left: 12px; padding: 2px 12px; font-size: 13px;">Bu Hafta</button>
		</div>
	`);
	$(page.body).prepend(headerRow);

	const tableContainer = $('<div id="work_orders_table"></div>');
	content.append(tableContainer);

	function formatDate(dt) {
		return dt ? String(dt).split(' ')[0] : '';
	}

	function getMonday(d) {
		d = new Date(d);
		let day = d.getDay();
		let diff = d.getDate() - day + (day === 0 ? -6 : 1);
		return new Date(d.setDate(diff));
	}

	function updateLabel(days) {
		if (!days || days.length === 0) return;
		const label = $('#current_label');
		const start = new Date(days[0].date);
		const end = new Date(days[days.length - 1].date);
		const format = d => `${String(d.getDate()).padStart(2,'0')} ${months[d.getMonth()]}`;
		label.text(`${format(start)} - ${format(end)}`);
	}

	function getColorForSalesOrder(salesOrder) {
		if (!salesOrder) return '#cdeffe';
		const palette = ['#FFA726', '#66BB6A', '#29B6F6', '#AB47BC', '#EF5350', '#FF7043', '#26C6DA', '#D4E157'];
		let hash = 0;
		for (let i = 0; i < salesOrder.length; i++) hash += salesOrder.charCodeAt(i);
		return palette[hash % palette.length];
	}
	function getStatusTone(status) {
		const tones = {
			'Planned': '#43e97b',
			'In Progress': '#ffd600',
			'Completed': '#42a5f5',
			'Cancelled': '#bdbdbd',
			'Overdue': '#ef5350'
		};
		return tones[status] || '#90caf9';
	}

	function load_work_orders_schedule() {
		let start = getMonday(currentDate);
		let end = new Date(start);
		end.setDate(start.getDate() + 6);
		let week_start = start.toISOString().slice(0, 10);
		let week_end = end.toISOString().slice(0, 10);

		$('#work_orders_table').html('<div style="text-align:center; color:#888; padding:40px;">Yükleniyor...</div>');

		frappe.call({
			method: 'uretim_planlama.uretim_planlama.api.get_weekly_work_orders',
			args: {
				week_start: week_start,
				week_end: week_end
			},
			callback: function(r) {
				if (r.message) {
					render_work_orders_table(r.message);
					updateLabel(r.message.days);
				} else {
					$('#work_orders_table').html('<div style="text-align:center; color:#888; padding:40px;">Kayıt bulunamadı.</div>');
				}
			}
		});
	}

	function render_work_orders_table(data) {
		const days = data.days || [];
		const salesOrders = data.sales_orders || {};
		
		// 1. Başlık satırı (günler)
		const header = $('<div style="display: flex; background: #f5f7fa; border-radius: 10px 10px 0 0; overflow: hidden; border-bottom: 2px solid #e0e0e0;"></div>');
		days.forEach(d => {
			let bgColor = d.isHoliday ? 'linear-gradient(90deg, #fbc2eb 0%, #f9d1d1 100%)' : (d.isWeekend ? '#b0b0b0' : 'linear-gradient(90deg, #e3f2fd 0%, #90caf9 100%)');
			let textColor = d.isHoliday ? '#c62828' : (d.isWeekend ? '#fff' : '#1565c0');
			let label = `${d.weekday} ${String(new Date(d.date).getDate()).padStart(2, '0')}.${String(new Date(d.date).getMonth() + 1).padStart(2, '0')}`;
			header.append(`<div style="width: 14.2857%; padding: 10px; font-weight: bold; background: ${bgColor}; color: ${textColor}; text-align:center; border-right: 1px solid #fff;">${label}</div>`);
		});

		// 2. Gövde (her günün iş emirleri)
		const body = $('<div style="display: flex; min-height: 90px; background: #fff;"></div>');
		days.forEach(d => {
			const dayJobs = [];
			Object.values(salesOrders).forEach(workOrders => {
				workOrders.forEach(wo => {
					const start = new Date(wo.planned_start_date);
					const end = new Date(wo.planned_end_date);
					const day = new Date(d.date);
					if (day >= start && day <= end) {
						dayJobs.push({
							...wo,
							color: getColorForSalesOrder(wo.sales_order),
							statusTone: getStatusTone(wo.status)
						});
					}
				});
			});
			const column = $('<div style="width: 14.2857%; padding: 6px 2px; min-height: 80px; border-right: 1px solid #eee; display: flex; flex-direction: column; align-items: stretch;"></div>');
			if (d.isHoliday && d.holidayReason && !(d.isWeekend && d.holidayReason === d.weekday)) {
				column.append(`<div style="font-size: 11px; color: #721c24; margin-bottom: 6px; text-align: center;">${d.holidayReason}</div>`);
			}
			dayJobs.forEach(job => {
				const badge = statusBadges[job.status] || { bg: '#90caf9', color: '#fff', label: job.status };
				const isWeekend = days.find(dd => dd.date === d.date)?.isWeekend;
				const blockOpacity = isWeekend ? 0.7 : 1;
				const blockTooltip = isWeekend ? 'Bu gün tatil, planlama için önerilmez.' : '';
				const getContrastYIQ = (hexcolor) => {
					hexcolor = hexcolor.replace('#', '');
					var r = parseInt(hexcolor.substr(0,2),16);
					var g = parseInt(hexcolor.substr(2,2),16);
					var b = parseInt(hexcolor.substr(4,2),16);
					var yiq = ((r*299)+(g*587)+(b*114))/1000;
					return (yiq >= 128) ? '#222' : '#fff';
				};
				const blockBg = job.color;
				const blockTextColor = getContrastYIQ(job.color);
				column.append(`
					<div class="work-order-block"
						data-wo='${encodeURIComponent(JSON.stringify(job))}'
						style="background:${blockBg}; color:${blockTextColor}; margin-bottom: 8px; padding: 8px 7px 8px 7px; border-radius: 10px; font-size: 11px; font-weight: 500; text-align:left; box-shadow:0 1px 6px #0002; opacity:${blockOpacity}; position:relative; min-height:54px; display:flex; flex-direction:column; align-items:flex-start; justify-content:flex-start; gap:2px; cursor:pointer;">
						<span class='wo-name-link' style='font-size:12px; font-weight:600; letter-spacing:0.5px; text-decoration:none; color:${blockTextColor}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; width:100%; display:block;'>${job.name}</span>
						<span style='font-size:10px; color:${blockTextColor}b0; margin-top:2px; margin-bottom:2px;'>P.Baş: ${formatDate(job.planned_start_date)}</span>
						<span style='font-size:10px; color:${blockTextColor}b0; flex:1; text-align:right;'>P.Bit: ${formatDate(job.planned_end_date)}</span>
						<span class='wo-status-badge' style='background:${badge.bg}; color:${badge.color}; border-radius:7px; font-size:10px; font-weight:700; padding:2px 10px; box-shadow:0 1px 4px #0001; position:absolute; right:7px; bottom:7px;'>${badge.label}</span>
					</div>
				`);
			});
			body.append(column);
		});

		// 3. Footer (özet)
		const footer = $('<div style="display: flex; border-top: 2px solid #bbb; background: #f8f9fa; font-size: 13px; font-weight: 500;"></div>');
		days.forEach((d, i) => {
			footer.append(`<div style="width: 14.2857%; padding: 6px 2px; text-align: center; color:#bbb;"> </div>`);
		});

		const table = $('<div style="overflow-x:auto; border-radius:12px; box-shadow:0 2px 12px #0001; margin-bottom:30px; background:#fff;"></div>');
		table.append(header);
		table.append(body);
		table.append(footer);
		$('#work_orders_table').empty().append(table);

		// Detay modalı açma eventini delegasyon ile bağla
		$('#work_orders_table').off('click', '.work-order-block').on('click', '.work-order-block', function(e) {
			const wo = JSON.parse(decodeURIComponent($(this).attr('data-wo')));
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.get_work_order_detail',
				args: { work_order_id: wo.name },
				callback: function(r) {
					if (!r.message) return;
					const job = r.message;
					const badge = statusBadges[job.status] || { bg: '#90caf9', color: '#fff', label: job.status };
					function formatDate(val) {
						if (!val || val === '-') return '-';
						const d = new Date(val);
						if (isNaN(d.getTime())) return val;
						return `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth()+1).toString().padStart(2, '0')}.${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
					}
					let html = `<div style="margin-bottom:12px;">
						<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">İş Emri</label><br>
							<a href="/app/work-order/${job.name}" target="_blank" style="font-weight:bold; color:#1976d2; text-decoration:underline;">${job.name}</a>
						</div>`;
					if (job.sales_order) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Satış Siparişi</label><br>
							<a href="/app/sales-order/${job.sales_order}" target="_blank" style="font-weight:bold; color:#f57c00; text-decoration:underline;">${job.sales_order}</a>
						</div>`;
					}
					if (job.bom_no) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">BOM Numarası</label><br>
							<a href="/app/bom/${job.bom_no}" target="_blank" style="font-weight:bold; color:#6d4c41; text-decoration:underline;">${job.bom_no}</a>
						</div>`;
					}
					if (job.production_plan) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Üretim Planı</label><br>
							<a href="/app/production-plan/${job.production_plan}" target="_blank" style="font-weight:bold; color:#009688; text-decoration:underline;">${job.production_plan}</a>
						</div>`;
					}
					html += `<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Durumu</label><br>
						<span style="display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background:${badge.bg}; color:${badge.color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">${badge.label}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Üretilecek Miktar</label><br>
						<span>${job.qty}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Üretilen Miktar</label><br>
						<span>${job.produced_qty}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Planlanan Başlangıç</label><br>
						<span>${formatDate(job.planned_start_date)}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Planlanan Bitiş</label><br>
						<span>${formatDate(job.planned_end_date)}</span>
					</div>
					<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Toplam Fiili Süre (dk)</label><br>
						<span>${job.total_time_in_mins !== undefined ? job.total_time_in_mins : '-'}</span>
					</div>`;
					// OPERASYONLAR TABLOSU
					if (Array.isArray(job.operations) && job.operations.length > 0) {
						html += `<div style="margin-bottom:8px;">
							<label style="font-size:12px;color:#888;">Operasyonlar</label><br>
							<table style='width:100%; border-collapse:collapse; font-size:12px; margin-top:4px;'>
								<tr style='background:#f5f5f5; font-weight:bold;'>
									<td style='padding:4px 6px;'>Operasyon</td>
									<td style='padding:4px 6px;'>İş İstasyonu</td>
									<td style='padding:4px 6px;'>Durum</td>
									<td style='padding:4px 6px;'>Üretilen</td>
									<td style='padding:4px 6px;'>Plan. Başlangıç</td>
									<td style='padding:4px 6px;'>Plan. Bitiş</td>
									<td style='padding:4px 6px;'>Fiili Başlangıç</td>
									<td style='padding:4px 6px;'>Fiili Bitiş</td>
								</tr>`;
							job.operations.forEach(op => {
								let status = op.status;
								// Pending veya Not Started ise ve actual_start_time var, actual_end_time yoksa Devam Ediyor say
								if (
									(status === 'Pending' || status === 'Not Started') &&
									op.actual_start_time && !op.actual_end_time
								) {
									status = 'In Progress';
								}
								const opBadge = operationStatusBadges[status] || { bg: '#ffd600', color: '#333', label: status };
								html += `<tr>
									<td style='padding:4px 6px;'>${op.operation}</td>
									<td style='padding:4px 6px;'>${op.workstation}</td>
									<td style='padding:4px 6px;'><span style='background:${opBadge.bg}; color:${opBadge.color}; border-radius:7px; font-size:11px; font-weight:600; padding:2px 8px;'>${opBadge.label}</span></td>
									<td style='padding:4px 6px;'>${op.completed_qty !== undefined ? op.completed_qty : '-'}</td>
									<td style='padding:4px 6px;'>${formatDate(op.planned_start_time)}</td>
									<td style='padding:4px 6px;'>${formatDate(op.planned_end_time)}</td>
									<td style='padding:4px 6px;'>${formatDate(op.actual_start_time)}</td>
									<td style='padding:4px 6px;'>${formatDate(op.actual_end_time)}</td>
								</tr>`;
							});
							html += `</table>
						</div>`;
					}
					const dialog = new frappe.ui.Dialog({
						title: 'İş Emri Detayı',
						size: 'large',
						fields: [
							{
								fieldtype: 'HTML',
								fieldname: 'work_order_html',
								options: html
							}
						],
						primary_action_label: 'Kapat',
						primary_action() { dialog.hide(); }
					});
					dialog.show();
				}
			});
		});
	}

	$('#today_btn').on('click', () => {
		currentDate = getMonday(new Date());
		load_work_orders_schedule();
	});

	$('#prev_btn').on('click', () => {
		currentDate.setDate(currentDate.getDate() - 7);
		load_work_orders_schedule();
	});

	$('#next_btn').on('click', () => {
		currentDate.setDate(currentDate.getDate() + 7);
		load_work_orders_schedule();
	});

	load_work_orders_schedule();
};
