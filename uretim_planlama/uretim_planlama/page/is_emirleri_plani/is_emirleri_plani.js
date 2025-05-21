// Global değişkenler
let currentDate = new Date();
const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
let calendar = null;
let holidaysMap = {};

// Statü etiketleri
const statusBadges = {
	'Not Started': { bg: '#ffd600', color: '#333', label: 'Açık' },
	'Completed':   { bg: '#43e97b', color: '#fff', label: 'Tamamlandı' },
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
	if (!salesOrder) return '#cdeffe';
	const palette = ['#FFA726', '#66BB6A', '#29B6F6', '#AB47BC', '#EF5350', '#FF7043', '#26C6DA', '#D4E157'];
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
			if (callback) callback();
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
		dayCellDidMount: function(arg) {
			const iso = getLocalISODate(arg.date);
			if (holidaysMap && holidaysMap[iso]) {
				arg.el.style.background = '#ffeaea';
				arg.el.title = holidaysMap[iso];
			} else if (arg.date.getDay() === 0 || arg.date.getDay() === 6) {
				arg.el.style.background = '#f5f5f5';
				arg.el.title = '';
			} else {
				arg.el.style.background = '';
				arg.el.title = '';
			}
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
							name: wo.id
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
			const so = data.sales_order ? `<span style='color:#333; font-size:9px; font-weight:500; margin-left:6px;'>${data.sales_order}</span>` : '';
			return {
				html: `
					<div style="display:flex; align-items:center; width:100%; background:${data.bg || '#e3f2fd'}; border-radius:4px; padding:1px 2px; min-height:18px; font-size:10px; font-weight:600; color:#222;">
						<span>${arg.event.title}${so}</span>
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
		}
	});

	calendar.render();
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
	fetchHolidays(start, end, function() {
		calendar.rerenderDates();
	});
}
