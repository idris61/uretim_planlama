// Global değişkenler
let currentDate = new Date();
const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
let calendar = null;
let holidaysMap = {};

// Statü etiketleri
const statusBadges = {
	'Not Started': { bg: '#ffd600', color: '#333', label: 'Açık' },
	'Completed':   { bg: '#43e97b', color: '#222', label: 'Tamamlandı' },
	'Draft':       { bg: '#bdbdbd', color: '#fff', label: 'Taslak' }
};

// Operasyonlar için özel badge haritası
const operationStatusBadges = {
	'Pending':      { bg: '#ffd600', color: '#333', label: 'Açık' },
	'Not Started':  { bg: '#ffd600', color: '#333', label: 'Açık' },
	'In Progress':  { bg: '#ff9800', color: '#fff', label: 'Devam Ediyor' },
	'In Process':   { bg: '#ff9800', color: '#fff', label: 'Devam Ediyor' },
	'Completed':    { bg: '#43e97b', color: '#fff', label: 'Tamamlandı' }
};

// Yardımcı fonksiyonlar
function formatDate(dt) {
	return dt ? String(dt).split(' ')[0] : '';
}

function getMonday(d) {
	d = new Date(d);
	let day = d.getDay();
	let diff = d.getDate() - day + (day === 0 ? -6 : 1);
	return new Date(d.setDate(diff));
}

function getColorForSalesOrder(salesOrder) {
	if (!salesOrder) return '#e3f2fd'; // Varsayılan pastel mavi
	// Pastel ve yumuşak renk paleti (gri ve pembe yok)
	const palette = [
		'#e3f2fd', // Açık mavi
		'#b2ebf2', // Açık turkuaz
		'#c8e6c9', // Açık yeşil
		'#d1c4e9', // Açık mor
		'#fff9c4', // Açık sarı
		'#b3e5fc', // Açık mavi
		'#b39ddb', // Açık mor
		'#dcedc8'  // Açık yeşil
	];
	let hash = 0;
	for (let i = 0; i < salesOrder.length; i++) hash += salesOrder.charCodeAt(i);
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
		let myCalendarDiv = $('<div id="my_custom_calendar" style="min-height:600px;"></div>');
		$('#work_orders_calendar').append(myCalendarDiv);
	}
	initializeCalendar();
});

frappe.provide('uretim_planlama');

frappe.pages['is_emirleri_plani'].on_page_load = function(wrapper) {
	// Sayfa oluştur
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
	navContainer.append(prevBtn);
	navContainer.append(todayBtn);
	navContainer.append(nextBtn);

	// Calendar container
	let calendarContainer = $('<div id="work_orders_calendar" style="margin-top:30px;"></div>');
	$(page.body).append(calendarContainer);

	// Takvim div'i oluştur
	if (!document.getElementById('my_custom_calendar')) {
		let myCalendarDiv = $('<div id="my_custom_calendar" style="min-height:600px;"></div>');
		$('#work_orders_calendar').append(myCalendarDiv);
	}

	// Navigation butonları için event listener'lar
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

	// İlk yükleme
	const today = new Date();
	const start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0,10);
	const end = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().slice(0,10);
	fetchHolidays(start, end, initializeCalendar);
}

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
		const day = new Date(date).getDay();
		// Önce eski açıklamayı sil
		$(this).find('.holiday-desc').remove();
		if (holidaysMap[date]) {
			$(this).addClass('holiday-override');
			$(this).attr('title', holidaysMap[date]);
			// Cumartesi/Pazar hariç açıklama ekle
			if (day !== 0 && day !== 6) {
				$(this).append(`<div class="holiday-desc">${holidaysMap[date]}</div>`);
			}
		} else if (day === 0) {
			$(this).addClass('holiday-override');
			$(this).attr('title', 'Pazar');
		} else if (day === 6) {
			$(this).addClass('holiday-override');
			$(this).attr('title', 'Cumartesi');
		} else {
			$(this).removeClass('holiday-override');
			$(this).attr('title', '');
		}
	});
}

// Yerel tarihi YYYY-MM-DD formatında döndürür
function getLocalISODate(date) {
	const year = date.getFullYear();
	const month = (date.getMonth() + 1).toString().padStart(2, '0');
	const day = date.getDate().toString().padStart(2, '0');
	return `${year}-${month}-${day}`;
}

function initializeCalendar() {
	if (typeof FullCalendar === 'undefined') return;
	
	var calendarEl = document.getElementById('my_custom_calendar');
	if (!calendarEl) return;

	if (calendar) {
		calendar.destroy();
	}

	calendar = new FullCalendar.Calendar(calendarEl, {
		initialView: 'dayGridMonth',
		height: 'auto',
		locale: 'tr',
		dayMaxEventRows: true,
		firstDay: 1,
		datesSet: function(info) {
			updateCalendarHolidays();
			updateDayCellBackgrounds();
		},
		dayCellDidMount: function(arg) {
			const iso = getLocalISODate(arg.date);
			arg.el.setAttribute('data-date', iso);
		},
		events: function(fetchInfo, successCallback, failureCallback) {
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.get_work_orders_for_calendar',
				args: {
					start: fetchInfo.startStr,
					end: fetchInfo.endStr
				},
				callback: function(r) {
					if (r.message) {
						const events = r.message.map(wo => ({
							title: wo.title,
							start: wo.start,
							end: wo.end,
							bg: getColorForSalesOrder(wo.sales_order),
							status: wo.status,
							sales_order: wo.sales_order,
							planned_start_date: formatDate(wo.start),
							planned_end_date: formatDate(wo.end),
							name: wo.id,
							editable: true
						}));
						successCallback(events);
					} else {
						successCallback([]);
					}
				},
				error: function() {
					failureCallback();
				}
			});
		},
		eventContent: function(arg) {
			const data = arg.event.extendedProps || {};
			const badge = statusBadges[data.status] || { bg: '#90caf9', color: '#fff', label: data.status };
			const so = data.sales_order ? `<span style='color:#222; font-size:12px; font-weight:bold; margin-left:6px;'>${data.sales_order}</span>` : '';
			return {
				html: `
					<div style="display:flex; align-items:center; justify-content:space-between; width:100%; background:${data.bg || '#64b5f6'}; border-radius:4px; padding:3px 7px; min-height:22px; font-size:13px; font-weight:500; color:#222; position:relative; border:1px solid rgba(0,0,0,0.07); box-shadow:0 1px 2px rgba(0,0,0,0.06);">
						<span style='font-weight:bold; font-size:13px;'>${arg.event.title}${so}</span>
						<span style="position:absolute; top:2px; right:2px; padding:1px 7px; border-radius:7px; font-size:11px; font-weight:600; background:${badge.bg}; color:${badge.color}; box-shadow:0 1px 2px rgba(0,0,0,0.1);">${badge.label}</span>
					</div>
				`
			};
		},
		eventDidMount: function(info) {
			const data = info.event.extendedProps || {};
			let tooltip = `İş Emri: ${info.event.title}\nSipariş No: ${data.sales_order || '-'}\nBaşlangıç: ${data.planned_start_date}\nBitiş: ${data.planned_end_date}\nDurum: ${data.status}`;
			info.el.title = tooltip;
		},
		eventClick: function(arg) {
			const data = arg.event.extendedProps;
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.get_work_order_detail',
				args: { work_order_id: data.name },
				callback: function(r) {
					if (!r.message) return;
					showWorkOrderDetails(r.message);
				}
			});
		},
		eventDrop: function(info) {
			const data = info.event.extendedProps || {};
			const newStart = info.event.start;
			const oldStart = info.oldEvent.start;
			const duration = info.event.end && info.event.start ? (info.event.end.getTime() - info.event.start.getTime()) : 0;
			const newEnd = duration ? new Date(newStart.getTime() + duration) : null;
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.update_work_order_date',
				args: {
					work_order_id: data.name,
					new_start: newStart.toISOString().slice(0,10),
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({message: 'Tarih güncellendi', indicator: 'green'});
						calendar.refetchEvents();
					} else {
						frappe.show_alert({message: 'Tarih güncellenemedi: ' + (r.message && r.message.error), indicator: 'red'});
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
		if ((status === 'Pending' || status === 'Not Started') && op.actual_start_time && !op.actual_end_time) {
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

	html += `</table></div>`;
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

function updateCalendarHolidays() {
	if (!calendar) return;
	const view = calendar.view;
	const start = view.currentStart.toISOString().slice(0,10);
	const end = view.currentEnd.toISOString().slice(0,10);
	fetchHolidays(start, end);
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
.fc .fc-event { border: none !important; background: transparent !important; }\
.fc .fc-event:hover { filter: brightness(0.98); }\
</style>').appendTo('head');
