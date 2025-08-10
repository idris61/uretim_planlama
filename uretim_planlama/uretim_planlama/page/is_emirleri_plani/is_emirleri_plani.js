// Global değişkenler
let currentDate = new Date();
const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
let calendar = null;
let holidaysMap = {};

// Status colors dosyasını yükle
frappe.require(['/assets/uretim_planlama/js/status_colors.js'], function() {
	if (!uretim_planlama?.status_colors) {
		frappe.msgprint({
			title: 'Hata',
			message: 'Durum renkleri yüklenemedi. Lütfen sayfayı yenileyin.',
			indicator: 'red'
		});
		return;
	}
	initializePage();
});

// Yardımcı fonksiyonlar
function formatDate(dt) {
	if (!dt) return '';
	try {
		// Geçerli bir tarih string'i mi kontrol et
		const date = new Date(dt);
		if (isNaN(date.getTime())) return '';
		// UTC tarihini kullan
		return date.toISOString().split('T')[0];
	} catch (e) {
		return '';
	}
}

function getMonday(d) {
	try {
		d = new Date(d);
		if (isNaN(d.getTime())) return new Date();
		// UTC'ye göre pazartesi gününü bul
		const day = d.getUTCDay();
		const diff = d.getUTCDate() - day + (day === 0 ? -6 : 1);
		return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), diff));
	} catch (e) {
		return new Date();
	}
}

function getColorForSalesOrder(salesOrder) {
	if (!salesOrder) return '#e3f2fd';
	const palette = [
		'#e3f2fd', '#b2ebf2', '#c8e6c9', '#d1c4e9',
		'#fff9c4', '#b3e5fc', '#b39ddb', '#dcedc8'
	];
	let hash = 0;
	for (let i = 0; i < salesOrder.length; i++) {
		hash += salesOrder.charCodeAt(i);
	}
	return palette[hash % palette.length];
}

// FullCalendar'ı CDN ile yükle
$('<link/>', {
	rel: 'stylesheet',
	type: 'text/css',
	href: 'https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css'
}).appendTo('head');

$.getScript('https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js', function() {
	if (!document.getElementById('my_custom_calendar')) {
		$('#work_orders_calendar').append('<div id="my_custom_calendar" style="min-height:600px;"></div>');
	}
	initializeCalendar();
});

frappe.provide('uretim_planlama');

frappe.pages['is_emirleri_plani'].on_page_load = function(wrapper) {
	// Status colors dosyasını yükle
	frappe.require(['/assets/uretim_planlama/js/status_colors.js'], function() {
		if (!uretim_planlama?.status_colors) {
			frappe.msgprint({
				title: 'Hata',
				message: 'Durum renkleri yüklenemedi. Lütfen sayfayı yenileyin.',
				indicator: 'red'
			});
			return;
		}
		
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'İş Emirleri Planı',
			single_column: true
		});

		// Navigation buttons
		let navContainer = $('<div style="display:flex; gap:10px; margin-bottom:20px;"></div>');
		$(page.body).append(navContainer);
		
		let prevBtn = $('<button class="btn btn-default" id="prev_btn">Önceki Ay</button>');
		let todayBtn = $('<button class="btn btn-default" id="today_btn">Bugün</button>');
		let nextBtn = $('<button class="btn btn-default" id="next_btn">Sonraki Ay</button>');
		navContainer.append(prevBtn, todayBtn, nextBtn);

		// Calendar container
		let calendarContainer = $('<div id="work_orders_calendar" style="margin-top:30px;"></div>');
		$(page.body).append(calendarContainer);

		if (!document.getElementById('my_custom_calendar')) {
			$('#work_orders_calendar').append('<div id="my_custom_calendar" style="min-height:600px;"></div>');
		}

		// Event handlers
		$('#today_btn').on('click', () => {
			if (calendar) {
				calendar.today();
				updateCalendarHolidays();
			}
		});

		$('#prev_btn').on('click', () => {
			if (calendar) {
				calendar.prev();
				updateCalendarHolidays();
			}
		});

		$('#next_btn').on('click', () => {
			if (calendar) {
				calendar.next();
				updateCalendarHolidays();
			}
		});

		// FullCalendar'ı CDN ile yükle
		$('<link/>', {
			rel: 'stylesheet',
			type: 'text/css',
			href: 'https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css'
		}).appendTo('head');

		$.getScript('https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js', function() {
			// İlk yükleme
			const today = new Date();
			const start = new Date(today.getFullYear(), today.getMonth(), 1);
			const end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
			fetchHolidays(
				start.toISOString().split('T')[0],
				end.toISOString().split('T')[0],
				initializeCalendar
			);
		});
	});
};

function fetchHolidays(start, end, callback) {
	frappe.call({
		method: 'uretim_planlama.uretim_planlama.api.get_holidays_for_calendar',
		args: { start, end },
		callback: function(r) {
			holidaysMap = r.message || {};
			updateDayCellBackgrounds();
			if (callback) callback();
		}
	});
}

function updateDayCellBackgrounds() {
	$('.fc-daygrid-day').each(function() {
		const date = $(this).data('date');
		if (!date) return;
		
		// UTC tarihini kullan
		const utcDate = new Date(date + 'T00:00:00Z');
		const day = utcDate.getUTCDay();
		
		$(this).find('.holiday-desc').remove();
		
		if (holidaysMap[date]) {
			$(this).addClass('holiday-override')
				.attr('title', holidaysMap[date]);
			if (day !== 0 && day !== 6) {
				$(this).append(`<div class="holiday-desc">${holidaysMap[date]}</div>`);
			}
		} else if (day === 0 || day === 6) {
			$(this).addClass('holiday-override')
				.attr('title', day === 0 ? 'Pazar' : 'Cumartesi');
		} else {
			$(this).removeClass('holiday-override')
				.attr('title', '');
		}
	});
}

function getLocalISODate(date) {
	// UTC tarihini kullan
	return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
}

function initializeCalendar() {
	if (typeof FullCalendar === 'undefined') {
		return;
	}
	
	var calendarEl = document.getElementById('my_custom_calendar');
	if (!calendarEl) {
		return;
	}

	if (calendar) {
		calendar.destroy();
	}

	calendar = new FullCalendar.Calendar(calendarEl, {
		initialView: 'dayGridMonth',
		height: 'auto',
		locale: 'tr',
		dayMaxEventRows: true,
		firstDay: 1,
		timeZone: 'UTC',
		datesSet: function() {
			updateCalendarHolidays();
			updateDayCellBackgrounds();
		},
		dayCellDidMount: function(arg) {
			try {
				const date = arg.date;
				if (date instanceof Date && !isNaN(date.getTime())) {
					arg.el.setAttribute('data-date', date.toISOString().split('T')[0]);
				}
			} catch (e) {
			}
		},
		events: function(fetchInfo, successCallback, failureCallback) {
			try {
				frappe.call({
					method: 'uretim_planlama.uretim_planlama.api.get_work_orders_for_calendar',
					args: {
						start: fetchInfo.startStr,
						end: fetchInfo.endStr,
						include_draft: true  // Taslak iş emirlerini dahil et
					},
					callback: function(r) {
						if (r.message) {
							const events = r.message.map(wo => {
								try {
									const isDraft = wo.status === 'Draft';
									let start = formatDate(wo.start);
									let end = formatDate(wo.end);
									if (isDraft && (!start || !end)) {
										const today = new Date();
										const todayStr = today.toISOString().split('T')[0];
										if (!start) start = todayStr;
										if (!end) end = todayStr;
									}
									if (!start || !end) return null;
									return {
										title: wo.title || '',
										start: start,
										end: end,
										bg: isDraft ? '#f5f5f5' : getColorForSalesOrder(wo.sales_order),
										status: wo.status || '',
										sales_order: wo.sales_order || '',
										planned_start_date: start,
										planned_end_date: end,
										name: wo.id || '',
										editable: isDraft ? true : false,  // Sadece taslak iş emirleri sürüklenebilir
										customer: wo.customer || '',
										custom_end_customer: wo.custom_end_customer || '',
										isDraft: isDraft  // Taslak durumu için ek özellik
									};
								} catch (e) {
									return null;
								}
							}).filter(Boolean);
							successCallback(events);
						} else {
							successCallback([]);
						}
					},
					error: function(err) {
						failureCallback(err);
					}
				});
			} catch (e) {
				failureCallback(e);
			}
		},
		eventContent: function(arg) {
			const data = arg.event.extendedProps || {};
			const badge = uretim_planlama.status_colors.getStatusBadge(data.status);
			const so = data.sales_order ? 
				`<span style='color:#222; font-size:12px; font-weight:bold; margin-left:6px;'>${data.sales_order}</span>` : '';
			
			// Taslak iş emirleri için özel stil
			const isDraft = data.isDraft;
			const draftStyle = isDraft ? 'border: 1px dashed #9e9e9e;' : '';
			const draftLabel = '';
			
			return {
				html: `
					<div style="display:flex; flex-direction:column; justify-content:flex-start; width:100%; 
						background:${isDraft ? '#f5f5f5' : (data.bg || '#64b5f6')}; border-radius:4px; padding:4px 8px; min-height:32px; 
						font-size:13px; font-weight:500; color:#222; position:relative; ${draftStyle} 
						box-shadow:0 1px 2px rgba(0,0,0,0.06); line-height:1.4; margin-bottom:4px; white-space:normal;">
						<span style='font-weight:bold; font-size:13px;'>${arg.event.title}</span>
						${data.sales_order ? `<span style='font-size:12px; color:#444; font-weight:bold;'>${data.sales_order}</span>` : ''}
						<span style="position:absolute; bottom:4px; right:8px; padding:1px 7px; border-radius:7px; 
							font-size:11px; font-weight:600; background:${badge.bg}; color:${badge.color}; 
							box-shadow:0 1px 2px rgba(0,0,0,0.1);">${badge.label}</span>
					</div>
				`
			};
		},
		eventDidMount: function(info) {
			const data = info.event.extendedProps || {};
			const badge = uretim_planlama.status_colors.getStatusBadge(data.status);
			// Modern tooltip HTML
			const tooltipHtml = `
				<div style="background:#fff; border-radius:10px; box-shadow:0 4px 16px rgba(0,0,0,0.13); padding:14px 18px; min-width:260px; max-width:340px; font-size:14px; color:#222;">
					<div style="font-size:16px; font-weight:700; color:#1976d2; margin-bottom:6px;">${info.event.title}</div>
					${data.sales_order ? `<div style='margin-bottom:4px;'><span style='color:#888;'>Sipariş No:</span> <span style='font-weight:600;'>${data.sales_order}</span></div>` : ''}
					${data.customer ? `<div style='margin-bottom:4px;'><span style='color:#888;'>Bayi:</span> <span style='font-weight:600;'>${data.customer}</span></div>` : ''}
					${data.custom_end_customer ? `<div style='margin-bottom:4px;'><span style='color:#888;'>Müşteri:</span> <span style='font-weight:600;'>${data.custom_end_customer}</span></div>` : ''}
					<div style='margin-bottom:4px; display:flex;'><span style='color:#888; min-width:110px;'>Planlanan Baş:</span><span>${data.planned_start_date}</span></div>
					<div style='margin-bottom:4px; display:flex;'><span style='color:#888; min-width:110px;'>Planlanan Bit:</span><span>${data.planned_end_date}</span></div>
					<div style='margin-bottom:4px;'><span style='color:#888;'>Durum:</span> <span style="background:${badge.bg}; color:${badge.color}; border-radius:7px; font-size:12px; font-weight:600; padding:2px 10px; display:inline-block;">${badge.label}</span></div>
				</div>
			`;
			// Remove default title
			info.el.title = '';
			// Custom tooltip on hover
			info.el.onmouseenter = function(e) {
				let tip = document.createElement('div');
				tip.className = 'fc-custom-tooltip';
				tip.innerHTML = tooltipHtml;
				tip.style.position = 'fixed';
				tip.style.zIndex = 9999;
				tip.style.pointerEvents = 'none';
				tip.style.left = (e.clientX + 16) + 'px';
				tip.style.top = (e.clientY + 8) + 'px';
				document.body.appendChild(tip);
				info.el.onmousemove = function(ev) {
					tip.style.left = (ev.clientX + 16) + 'px';
					tip.style.top = (ev.clientY + 8) + 'px';
				};
				info.el.onmouseleave = function() {
					if (tip && tip.parentNode) tip.parentNode.removeChild(tip);
					info.el.onmousemove = null;
					info.el.onmouseleave = null;
				};
			};
		},
		eventClick: function(arg) {
			const data = arg.event.extendedProps;
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.get_work_order_detail',
				args: { work_order_id: data.name },
				callback: function(r) {
					if (r.message) {
						showWorkOrderDetails(r.message);
					}
				}
			});
		},
		eventDrop: function(info) {
			const data = info.event.extendedProps || {};
			const newStart = info.event.start;
			const duration = info.event.end && info.event.start ? 
				(info.event.end.getTime() - info.event.start.getTime()) : 0;
			
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.update_work_order_date',
				args: {
					work_order_id: data.name,
					new_start: newStart.toISOString().slice(0,10),
				},
				callback: function(r) {
					if (r.message?.success) {
						frappe.show_alert({message: 'Tarih güncellendi', indicator: 'green'});
						calendar.refetchEvents();
					} else {
						frappe.show_alert({
							message: 'Tarih güncellenemedi: ' + (r.message?.error || 'Bilinmeyen hata'),
							indicator: 'red'
						});
						info.revert();
					}
				},
				error: function() {
					frappe.show_alert({message: 'Sunucu hatası!', indicator: 'red'});
					info.revert();
				}
			});
		}
	});

	calendar.render();
	updateDayCellBackgrounds();
}

function showWorkOrderDetails(job) {
	const badge = uretim_planlama.status_colors.getStatusBadge(job.status);

	function formatDate(val) {
		if (!val || val === '-') return "<span style='color:#bbb;font-style:italic;'>-</span>";
		try {
			const d = new Date(val);
			if (isNaN(d.getTime())) return val;
			return `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth()+1).toString().padStart(2, '0')}.${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
		} catch (e) {
			return val;
		}
	}

	function buildHtml(job, salesOrder) {
		try {
			let html = `<div style="margin-bottom:12px;">
				<div style="margin-bottom:8px;">
					<label style="font-size:12px;color:#888;">İş Emri</label><br>
					<a href="/app/work-order/${job.name || ''}" target="_blank" style="font-weight:bold; color:#1976d2; text-decoration:underline;">${job.name || '-'}</a>
				</div>`;

			if (job.sales_order) {
				html += `<div style="margin-bottom:8px;">
					<label style="font-size:12px;color:#888;">Satış Siparişi</label><br>
					<a href="/app/sales-order/${job.sales_order}" target="_blank" style="font-weight:bold; color:#f57c00; text-decoration:underline;">${job.sales_order}</a>
				</div>`;
			}

			if (salesOrder) {
				if (salesOrder.customer) {
					html += `<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Bayi</label><br>
						<span style="font-weight:bold; color:#f70404">${salesOrder.customer}</span>
					</div>`;
				}
				if (salesOrder.custom_end_customer) {
					html += `<div style="margin-bottom:8px;">
						<label style="font-size:12px;color:#888;">Müşteri</label><br>
						<span style="font-weight:bold; color:#10fb07">${salesOrder.custom_end_customer}</span>
					</div>`;
				}
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
				<span>${job.qty || '0'}</span>
			</div>
			<div style="margin-bottom:8px;">
				<label style="font-size:12px;color:#888;">Üretilen Miktar</label><br>
				<span>${job.produced_qty || '0'}</span>
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
				<span>${job.total_time_in_mins || '-'}</span>
			</div>`;

			if (Array.isArray(job.operations) && job.operations.length > 0) {
				html += `<div style="margin-bottom:8px;">
					<table style="width:100%; border-collapse:collapse; font-size:12px;">
						<thead>
							<tr style="background:#f5f5f5; font-weight:bold;">
								<th style="padding:4px 2px; width:15%;">Operasyon</th>
								<th style="padding:4px 2px; width:12%;">Durum</th>
								<th style="padding:4px 2px; width:8%; text-align:center;">Üret.</th>
								<th style="padding:4px 2px; width:16%;">Plan. Başl.</th>
								<th style="padding:4px 2px; width:16%;">Plan. Bitiş</th>
								<th style="padding:4px 2px; width:16%;">Fiili Başl.</th>
								<th style="padding:4px 2px; width:16%;">Fiili Bitiş</th>
							</tr>
						</thead>
						<tbody>`;
				job.operations.forEach(op => {
					let status = op.status;
					if ((status === 'Pending' || status === 'Not Started') && op.actual_start_time && !op.actual_end_time) {
						status = 'In Process';
					}
					const opBadge = uretim_planlama.status_colors.getOperationStatusBadge(status);
					html += `<tr style="border-bottom:1px solid #eee;">
						<td style="padding:3px 2px;">${op.operation || "<span style='color:#bbb;font-style:italic;'>-</span>"}</td>
						<td style="padding:3px 2px; text-align:center;"><span style="background:${opBadge.bg}; color:${opBadge.color}; border-radius:7px; font-size:11px; font-weight:600; padding:2px 8px; display:inline-block; min-width:60px; text-align:center;">${opBadge.label}</span></td>
						<td style="padding:3px 2px; text-align:center;">${op.completed_qty ?? "<span style='color:#bbb;font-style:italic;'>-</span>"}</td>
						<td style="padding:3px 2px;">${formatDate(op.planned_start_time)}</td>
						<td style="padding:3px 2px;">${formatDate(op.planned_end_time)}</td>
						<td style="padding:3px 2px;">${formatDate(op.actual_start_time)}</td>
						<td style="padding:3px 2px;">${formatDate(op.actual_end_time)}</td>
					</tr>`;
				});
				html += `</tbody></table></div>`;
			}
			return html;
		} catch (e) {
			return '<div style="color:red;">Detaylar görüntülenirken bir hata oluştu.</div>';
		}
	}

	try {
		if (job.sales_order) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Sales Order',
					name: job.sales_order
				},
				callback: function(r) {
					const salesOrder = r.message || {};
					const html = buildHtml(job, salesOrder);
					showModal(html);
				},
				error: function(err) {
					const html = buildHtml(job, null);
					showModal(html);
				}
			});
		} else {
			const html = buildHtml(job, null);
			showModal(html);
		}
	} catch (e) {
		frappe.msgprint({
			title: 'Hata',
			message: 'Detaylar görüntülenirken bir hata oluştu.',
			indicator: 'red'
		});
	}
}

function showModal(html) {
	try {
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
			primary_action() { 
				dialog.hide();
			}
		});
		dialog.show();
	} catch (e) {
		frappe.msgprint({
			title: 'Hata',
			message: 'Detay penceresi açılırken bir hata oluştu.',
			indicator: 'red'
		});
	}
}

function updateCalendarHolidays() {
	if (!calendar) return;
	const view = calendar.view;
	fetchHolidays(
		view.currentStart.toISOString().slice(0,10),
		view.currentEnd.toISOString().slice(0,10)
	);
}

$('<style>\
.fc .fc-col-header-cell { font-weight: bold !important; background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%) !important; color: #1565c0 !important; font-size: 16px !important; letter-spacing: 0.5px; }\
.fc .fc-col-header-cell.fc-day-sat, .fc .fc-col-header-cell.fc-day-sun { background: #fce4ec !important; color: #c2185b !important; }\
.fc .fc-daygrid-day-number { font-weight: bold; font-size: 15px; color: #1976d2; }\
.fc .fc-daygrid-day.holiday-override { position: relative; }\
.fc .fc-daygrid-day .holiday-desc { position: absolute; top: 2px; left: 2px; right: 2px; background: #fce4ec; color: #c2185b; font-size: 11px; font-weight: 600; border-radius: 4px; padding: 1px 2px; z-index: 2; text-align: center; pointer-events: none; }\
.fc .fc-daygrid-day { background: #ffffff !important; }\
.fc .fc-daygrid-day.fc-day-today { background: #f5f9ff !important; }\
.fc .fc-daygrid-day.fc-day-past { background: #fafafa !important; }\
.fc .fc-event { font-size: 13px !important; line-height: 1.4 !important; min-height: 28px !important; padding: 4px 8px !important; margin-bottom: 4px !important; white-space: normal !important; width: 100% !important; max-width: 100% !important; min-width: 0 !important; box-sizing: border-box !important; position: relative !important; background: none !important; border: none !important; }\
.fc .fc-event .fc-event-title { font-size: 13px !important; font-weight: 600 !important; }\
</style>').appendTo('head');
