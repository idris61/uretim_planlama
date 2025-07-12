import frappe
from frappe.utils import getdate, add_days, get_datetime
from datetime import timedelta
from calendar import monthrange
import pandas as pd
from collections import defaultdict
from frappe import _

day_name_tr = {
    'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
    'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
}

status_map = {
    "In Process": "Devam ediyor",
    "Completed": "Tamamlandı",
    "Not Started": "Açık",
    "Açık": "Açık",
    "Devam ediyor": "Devam ediyor",
    "Tamamlandı": "Tamamlandı",
    "İptal Edildi": "İptal Edildi"
}

@frappe.whitelist()
def get_weekly_production_schedule(year=None, month=None, week_start=None, week_end=None, workstation=None, status=None):
    if year and month:
        start_date = getdate(f"{year}-{month}-01")
        last_day = monthrange(int(year), int(month))[1]
        end_date = getdate(f"{year}-{month}-{last_day}")
    elif week_start and week_end:
        start_date = getdate(week_start)
        end_date = getdate(week_end)
    else:
        start_date = getdate()
        end_date = add_days(start_date, 6)

    while start_date.weekday() != 0:
        start_date -= timedelta(days=1)

    workstation_filters = {"name": workstation} if workstation else {}
    workstations = frappe.get_all('Workstation', filters=workstation_filters, fields=['name', 'holiday_list'])

    # Tüm operasyonları topluca çek
    operation_filters = {
        'planned_start_time': ['between', [str(start_date), f"{str(end_date)} 23:59:59"]]
    }
    if workstation:
        operation_filters['workstation'] = workstation
    if status:
        operation_filters['status'] = status
    all_operations = frappe.get_all('Work Order Operation',
        filters=operation_filters,
        fields=[
            'name', 'parent as work_order', 'operation', 'workstation',
            'planned_start_time', 'planned_end_time', 'status',
            'actual_start_time', 'actual_end_time', 'time_in_mins',
            'completed_qty'
        ]
    )
    # Tüm work order isimlerini topla
    work_order_names = list(set([op['work_order'] for op in all_operations]))
    # Tüm work order'ları topluca çek
    work_orders = {wo.name: wo for wo in frappe.get_all('Work Order', filters={'name': ['in', work_order_names]}, fields=['name','item_name','production_item','bom_no','sales_order','produced_qty'])}
    # Tüm sales order isimlerini topla
    sales_order_names = list(set([wo.sales_order for wo in work_orders.values() if wo.sales_order]))
    # Tüm sales order'ları topluca çek (customer ve custom_end_customer ile)
    sales_orders = {}
    if sales_order_names:
        for so in frappe.get_all('Sales Order', filters={'name': ['in', sales_order_names]}, fields=['name', 'customer', 'custom_end_customer']):
            sales_orders[so.name] = so
    # Tüm job card'ları topluca çek
    job_cards = frappe.get_all('Job Card', filters={'work_order': ['in', work_order_names]}, fields=['name','work_order','operation','for_quantity','status','total_completed_qty'])
    job_card_map = {}
    for jc in job_cards:
        key = (jc['work_order'], jc['operation'])
        job_card_map[key] = jc

    schedule = []
    for ws in workstations:
        ws_ops = [op for op in all_operations if op['workstation'] == ws.name]
        # Çalışma saatlerini child table'dan çek
        ws_doc = frappe.get_doc('Workstation', ws.name)
        work_hours = []
        for row in getattr(ws_doc, 'working_hours', []):
            if getattr(row, 'enabled', 1):
                work_hours.append({
                    'start_time': row.start_time,
                    'end_time': row.end_time
                })
        daily_work_minutes = {}
        from datetime import datetime
        for i in range(7):
            total = 0
            for wh in work_hours:
                s = datetime.strptime(str(wh['start_time']), '%H:%M:%S')
                e = datetime.strptime(str(wh['end_time']), '%H:%M:%S')
                diff = (e - s).seconds // 60
                total += diff
            daily_work_minutes[i] = total
        day_schedule = {}
        ops_in_this_week = set()
        total_hours = 0
        total_operations = 0
        daily_summary = {}
        if work_hours:
            for i in range(7):
                total = 0
                for wh in work_hours:
                    start = wh['start_time']
                    end = wh['end_time']
                    s = datetime.strptime(str(start), '%H:%M:%S') if ':' in str(start) else datetime.strptime(str(start), '%H:%M')
                    e = datetime.strptime(str(end), '%H:%M:%S') if ':' in str(end) else datetime.strptime(str(end), '%H:%M')
                    diff = (e-s).seconds // 60
                    total += diff
                daily_work_minutes[i] = total
        else:
            for i in range(7):
                daily_work_minutes[i] = 0
        for op in ws_ops:
            ops_in_this_week.add(op['operation'])
            work_order = work_orders.get(op['work_order'], {})
            job_card = job_card_map.get((op['work_order'], op['operation']))
            op_status = ''
            if job_card and job_card.get('status'):
                op_status = job_card['status']
            elif op['completed_qty'] > 0:
                op_status = 'Devam Ediyor'
            elif op['actual_start_time']:
                op_status = 'Başladı'
            start_dt = get_datetime(op['planned_start_time'])
            end_dt = get_datetime(op['planned_end_time'])
            time_in_mins = int((end_dt - start_dt).total_seconds() // 60) if start_dt and end_dt else 0
            total_hours += time_in_mins / 60
            total_operations += 1
            daily_summary.setdefault(day_name_tr[start_dt.strftime('%A')], {'planned_minutes': 0, 'jobs': 0})
            daily_summary[day_name_tr[start_dt.strftime('%A')]]['planned_minutes'] += time_in_mins
            daily_summary[day_name_tr[start_dt.strftime('%A')]]['jobs'] += 1
            # İlgili sales order'dan bayi ve müşteri bilgisini çek
            so = sales_orders.get(work_order.get('sales_order')) if work_order.get('sales_order') else None
            customer = so['customer'] if so and so.get('customer') else ''
            custom_end_customer = so['custom_end_customer'] if so and so.get('custom_end_customer') else ''
            day_schedule.setdefault(day_name_tr[start_dt.strftime('%A')], []).append({
                'name': job_card['name'] if job_card else "",
                'status': job_card['status'] if job_card and job_card.get('status') else status_map.get(op['status'] or "", "Tanımsız"),
                'qty_to_manufacture': job_card['for_quantity'] if job_card else 0,
                'total_completed_qty': work_order.get('produced_qty', 0),
                'item_name': work_order.get('item_name', ''),
                'production_item': work_order.get('production_item', ''),
                'bom_no': work_order.get('bom_no', ''),
                'sales_order': work_order.get('sales_order', ''),
                'customer': customer,
                'custom_end_customer': custom_end_customer,
                'work_order': op['work_order'],
                'operation': op['operation'] or 'Operasyon Yok',
                'color': get_color_for_sales_order(work_order.get('sales_order', '')),
                'start_time': start_dt.strftime('%Y-%m-%d %H:%M'),
                'end_time': end_dt.strftime('%Y-%m-%d %H:%M'),
                'expected_start_date': op['planned_start_time'],
                'expected_end_date': op['planned_end_time'],
                'actual_start_date': op['actual_start_time'],
                'actual_end_date': op['actual_end_time'],
                'total_time_in_mins': int((end_dt - start_dt).total_seconds() // 60),
                'time': f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}",
                'employee': "",
                'duration': time_in_mins,
                'op_status': op_status
            })
        daily_info = {}
        for i, day in enumerate(['Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi','Pazar']):
            planned = daily_summary.get(day, {}).get('planned_minutes', 0)
            jobs = daily_summary.get(day, {}).get('jobs', 0)
            work_min = daily_work_minutes.get(i, 0)
            doluluk = int((planned / work_min) * 100) if work_min > 0 else 0
            daily_info[day] = {
                'work_minutes': work_min,
                'planned_minutes': planned,
                'jobs': jobs,
                'doluluk': doluluk
            }
        if day_schedule:
            schedule.append({
                'name': ws.name,
                'schedule': day_schedule,
                'operations': sorted(list(ops_in_this_week)),
                'total_hours': round(total_hours, 1),
                'total_operations': total_operations,
                'work_hours': work_hours,
                'daily_info': daily_info
            })
    week_dates = get_week_dates(start_date)
    # Sadece ilgili istasyonların holiday_list'leri ile holiday sorgusu
    holiday_lists = list(set([ws['holiday_list'] for ws in workstations if ws.get('holiday_list')]))
    holidays = []
    for hl in holiday_lists:
        for h in frappe.get_all('Holiday', filters={'parent': hl, 'holiday_date': ['between', [start_date, end_date]]}, fields=['holiday_date', 'description']):
            holidays.append({
                'date': str(h.holiday_date),
                'reason': h.description or 'Tatil'
            })
    holiday_map = {h['date']: h['reason'] for h in holidays}
    days = []
    for d in week_dates:
        iso = d.strftime('%Y-%m-%d')
        weekday = day_name_tr[d.strftime('%A')]
        is_weekend = d.weekday() >= 5
        is_holiday = iso in holiday_map
        days.append({
            "date": d,
            "iso": iso,
            "weekday": weekday,
            "isWeekend": is_weekend,
            "isHoliday": is_holiday,
            "holidayReason": holiday_map[iso] if is_holiday else ""
        })
    return {
        'workstations': schedule,
        'holidays': holidays,
        'start_date': start_date.strftime("%d-%m-%Y"),
        'end_date': end_date.strftime("%d-%m-%Y"),
        'days': days
    }

def get_color_for_sales_order(sales_order):
    if not sales_order:
        return "#cdeffe"
    color_palette = ["#FFA726", "#66BB6A", "#29B6F6", "#AB47BC", "#EF5350", "#FF7043", "#26C6DA", "#D4E157"]
    return color_palette[sum(ord(c) for c in sales_order) % len(color_palette)]

def get_holidays(start_date, end_date):
    holidays = []
    for hl in frappe.get_all('Holiday List', fields=['name']):
        for h in frappe.get_all('Holiday',
            filters={'parent': hl.name, 'holiday_date': ['between', [start_date, end_date]]},
            fields=['holiday_date', 'description']
        ):
            holidays.append({
                'date': str(h.holiday_date),
                'reason': h.description or 'Tatil'
            })
    return holidays

def get_week_dates(start_date):
    # Pazartesi'den başlat
    monday = start_date - timedelta(days=start_date.weekday())
    # Haftanın günlerini oluştur
    return [monday + timedelta(days=i) for i in range(7)]

@frappe.whitelist()
def reschedule_operation(work_order, operation, new_date):
    try:
        work_order_op = frappe.get_list('Work Order Operation',
            filters={'parent': work_order, 'operation': operation},
            fields=['name', 'planned_start_time', 'planned_end_time']
        )
        if not work_order_op:
            frappe.throw('Operasyon bulunamadı')

        op = frappe.get_doc('Work Order Operation', work_order_op[0].name)
        current_start = get_datetime(op.planned_start_time)
        duration = get_datetime(op.planned_end_time) - current_start

        new_start = get_datetime(f"{new_date} {current_start.strftime('%H:%M:%S')}")
        new_end = new_start + duration

        op.planned_start_time = new_start
        op.planned_end_time = new_end
        op.save()
        frappe.db.commit()
        return True

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Operasyon Yeniden Planlama Hatası')
        frappe.throw(str(e))

@frappe.whitelist()
def export_schedule(start_date, end_date, workstation=None, status=None):
    try:
        data = get_weekly_production_schedule(
            week_start=start_date,
            week_end=end_date,
            workstation=workstation,
            status=status
        )

        rows = []
        for ws in data['workstations']:
            for day, operations in ws['schedule'].items():
                for op in operations:
                    rows.append({
                        'İş İstasyonu': ws['name'],
                        'Gün': day,
                        'Operasyon': op['operation'],
                        'İş Emri': op['work_order'],
                        'Ürün': op['item_name'],
                        'Miktar': op['qty_to_manufacture'],
                        'Durum': op['status'],
                        'Başlangıç': op['start_time'],
                        'Bitiş': op['end_time'],
                        'Çalışan': op.get('employee', ''),
                        'Süre (dk)': op.get('duration', 0)
                    })

        if not rows:
            frappe.throw('Dışa aktarılacak veri bulunamadı')

        df = pd.DataFrame(rows)
        file_name = f'uretim_planlama_{start_date}_{end_date}.xlsx'
        file_path = frappe.get_site_path('private', 'files', file_name)

        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Üretim Planı')
            worksheet = writer.sheets['Üretim Planı']
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_length)

        return f'/private/files/{file_name}'

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Üretim Planı Dışa Aktarma Hatası')
        frappe.throw(str(e))

@frappe.whitelist()
def get_weekly_work_orders(week_start=None, week_end=None, workstation=None, sales_order=None, status=None):
    from frappe.utils import getdate
    from datetime import timedelta
    if week_start and week_end:
        start_date = getdate(week_start)
        end_date = getdate(week_end)
    else:
        start_date = getdate()
        end_date = start_date + timedelta(days=6)
    # Pazartesi'ye çek
    while start_date.weekday() != 0:
        start_date -= timedelta(days=1)
    filters = {
        'planned_start_date': ['<=', end_date],
        'planned_end_date': ['>=', start_date]
    }
    if workstation:
        filters['workstation'] = workstation
    if sales_order:
        filters['sales_order'] = sales_order
    if status:
        filters['status'] = status
    work_orders = frappe.get_all('Work Order',
        filters=filters,
        fields=['name', 'sales_order', 'status', 'planned_start_date', 'planned_end_date', 'bom_no', 'production_plan', 'produced_qty']
    )
    # Satış siparişine göre gruplama
    sales_order_map = {}
    for wo in work_orders:
        so = wo.sales_order or 'Diğer'
        if so not in sales_order_map:
            sales_order_map[so] = []
        # Operasyon bilgisi (ilk operation child'ı)
        op_info = ''
        op_child = frappe.get_all('Work Order Operation', filters={'parent': wo.name}, fields=['operation'], limit=1)
        if op_child:
            op_info = op_child[0].operation
        wo['operation_info'] = op_info
        sales_order_map[so].append(wo)
    # Haftanın günleri
    week_dates = get_week_dates(start_date)
    days = []
    for d in week_dates:
        iso = d.strftime('%Y-%m-%d')
        weekday = day_name_tr[d.strftime('%A')]
        is_weekend = d.weekday() >= 5
        days.append({
            'date': d,
            'iso': iso,
            'weekday': weekday,
            'isWeekend': is_weekend
        })
    return {
        'sales_orders': sales_order_map,
        'days': days,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }

@frappe.whitelist()
def get_job_card_detail(job_card_id):
    job_card = frappe.get_doc('Job Card', job_card_id)
    return {
        'name': getattr(job_card, 'name', ''),
        'status': getattr(job_card, 'status', ''),
        'work_order': getattr(job_card, 'work_order', ''),
        'sales_order': getattr(job_card, 'sales_order', ''),
        'item_name': getattr(job_card, 'item_name', ''),
        'production_item': getattr(job_card, 'production_item', ''),
        'bom_no': getattr(job_card, 'bom_no', ''),
        'for_quantity': getattr(job_card, 'for_quantity', getattr(job_card, 'qty', '')),
        'total_completed_qty': getattr(job_card, 'total_completed_qty', getattr(job_card, 'completed_qty', '')),
        'operation': getattr(job_card, 'operation', ''),
        'expected_start_date': getattr(job_card, 'expected_start_date', getattr(job_card, 'from_time', getattr(job_card, 'planned_start_time', ''))),
        'expected_end_date': getattr(job_card, 'expected_end_date', getattr(job_card, 'to_time', getattr(job_card, 'planned_end_time', ''))),
        'actual_start_date': getattr(job_card, 'actual_start_date', getattr(job_card, 'actual_start_time', '')),
        'actual_end_date': getattr(job_card, 'actual_end_date', getattr(job_card, 'actual_end_time', '')),
        'total_time_in_mins': getattr(job_card, 'total_time_in_mins', getattr(job_card, 'time_in_mins', '')),
        'time_required': getattr(job_card, 'time_required', getattr(job_card, 'planned_operating_time', ''))
    }

@frappe.whitelist()
def get_work_order_detail(work_order_id):
    wo = frappe.get_doc('Work Order', work_order_id)
    operations = []
    # Operasyonlar child tablosu
    op_children = frappe.get_all('Work Order Operation', filters={'parent': work_order_id}, fields=[
        'operation', 'workstation', 'status', 'completed_qty', 'planned_start_time', 'planned_end_time', 'actual_start_time', 'actual_end_time', 'time_in_mins'
    ], order_by='planned_start_time asc')
    # İlgili iş kartlarını çek (doğru alanlarla)
    job_cards = frappe.get_all('Job Card', filters={'work_order': work_order_id}, fields=[
        'operation', 'status', 'actual_start_date', 'actual_end_date'
    ])
    job_card_map = {jc['operation']: jc for jc in job_cards}
    for op in op_children:
        jc = job_card_map.get(op['operation'])
        status = jc['status'] if jc and jc.get('status') else op.get('status', '')
        actual_start = jc['actual_start_date'] if jc and jc.get('actual_start_date') else op.get('actual_start_time', '')
        actual_end = jc['actual_end_date'] if jc and jc.get('actual_end_date') else op.get('actual_end_time', '')
        planned_start = op.get('planned_start_time')
        planned_end = op.get('planned_end_time')
        time_str = ''
        if planned_start and planned_end:
            try:
                from frappe.utils import get_datetime
                s = get_datetime(planned_start)
                e = get_datetime(planned_end)
                time_str = f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')}"
            except:
                time_str = ''
        operations.append({
            'operation': op.get('operation', ''),
            'workstation': op.get('workstation', ''),
            'status': status,
            'completed_qty': op.get('completed_qty', ''),
            'planned_start_time': planned_start,
            'planned_end_time': planned_end,
            'time': time_str,
            'actual_start_time': actual_start,
            'actual_end_time': actual_end,
            'duration': op.get('time_in_mins', '')
        })
    return {
        'name': getattr(wo, 'name', ''),
        'status': getattr(wo, 'status', ''),
        'sales_order': getattr(wo, 'sales_order', ''),
        'bom_no': getattr(wo, 'bom_no', ''),
        'production_plan': getattr(wo, 'production_plan', ''),
        'qty': getattr(wo, 'qty', ''),
        'produced_qty': getattr(wo, 'produced_qty', ''),
        'planned_start_date': getattr(wo, 'planned_start_date', getattr(wo, 'from_time', '')),
        'planned_end_date': getattr(wo, 'planned_end_date', getattr(wo, 'to_time', '')),
        'total_time_in_mins': getattr(wo, 'total_time_in_mins', getattr(wo, 'time_in_mins', '')),
        'operations': operations
    }

@frappe.whitelist()
def get_work_orders_for_calendar(start, end, include_draft=False):
    """
    Frappe Calendar için iş emirlerini döndürür.
    start ve end parametreleri takvimde gösterilecek aralığı belirtir.
    include_draft parametresi taslak iş emirlerinin dahil edilip edilmeyeceğini belirtir.
    """
    import datetime
    # Onaylanmış iş emirleri (tarih filtresi ile)
    approved_wos = frappe.get_all(
        "Work Order",
        fields=["name", "planned_start_date", "planned_end_date", "status", "sales_order", "docstatus"],
        filters={
            "docstatus": 1,
            "planned_start_date": ["<=", end],
            "planned_end_date": [">=", start]
        }
    )
    # Taslak iş emirleri (tarih filtresi olmadan)
    draft_wos = []
    if include_draft:
        draft_wos = frappe.get_all(
            "Work Order",
            fields=["name", "planned_start_date", "planned_end_date", "status", "sales_order", "docstatus"],
            filters={
                "docstatus": 0
            }
        )
    work_orders = approved_wos + draft_wos

    # Sales Order bilgilerini topluca çek
    sales_order_names = list(set([wo.sales_order for wo in work_orders if wo.sales_order]))
    sales_orders = {}
    if sales_order_names:
        for so in frappe.get_all("Sales Order", filters={"name": ["in", sales_order_names]}, fields=["name", "customer", "custom_end_customer"]):
            sales_orders[so.name] = so

    today_str = datetime.date.today().strftime('%Y-%m-%d')
    events = []
    for wo in work_orders:
        customer = None
        custom_end_customer = None
        if wo.sales_order and wo.sales_order in sales_orders:
            customer = sales_orders[wo.sales_order].customer
            custom_end_customer = sales_orders[wo.sales_order].custom_end_customer
        # Status yönetimi:
        status = "Draft" if wo.docstatus == 0 else (wo.status or "Not Started")
        # Taslak iş emirlerinde tarih yoksa bugünün tarihini ata
        start_date = wo.planned_start_date or (today_str if wo.docstatus == 0 else None)
        end_date = wo.planned_end_date or (today_str if wo.docstatus == 0 else None)
        # Saatleri ayarla
        if wo.docstatus == 1 and start_date:
            try:
                # ISO 8601 formatını işle
                if 'T' in str(start_date):
                    dt = datetime.datetime.fromisoformat(str(start_date).replace('Z', '+00:00'))
                else:
                    # Eski format için
                    dt = datetime.datetime.strptime(str(start_date), '%Y-%m-%d' if len(str(start_date))==10 else '%Y-%m-%d %H:%M:%S')
                start_date = dt.replace(hour=8, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
                end_date = (dt.replace(hour=9, minute=0, second=0)).strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Hata durumunda varsayılan değerleri kullan
                start_date = None
                end_date = None
        elif wo.docstatus == 0 and start_date:
            try:
                # ISO 8601 formatını işle
                if 'T' in str(start_date):
                    dt = datetime.datetime.fromisoformat(str(start_date).replace('Z', '+00:00'))
                else:
                    # Eski format için
                    dt = datetime.datetime.strptime(str(start_date), '%Y-%m-%d' if len(str(start_date))==10 else '%Y-%m-%d %H:%M:%S')
                start_date = dt.replace(hour=8, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
                end_date = start_date
            except ValueError:
                # Hata durumunda varsayılan değerleri kullan
                start_date = None
                end_date = None
        # Eğer onaylanmış iş emrinde tarih yoksa, event ekleme
        if wo.docstatus == 1 and (not start_date or not end_date):
            continue
        events.append({
            "id": wo.name,
            "title": wo.name,
            "start": start_date,
            "end": end_date,
            "status": status,
            "sales_order": wo.sales_order,
            "customer": customer,
            "custom_end_customer": custom_end_customer,
            "is_draft": wo.docstatus == 0
        })
    return events

@frappe.whitelist()
def get_holidays_for_calendar(start, end):
    holidays = {}
    for hl in frappe.get_all('Holiday List', fields=['name']):
        for h in frappe.get_all('Holiday',
            filters={'parent': hl.name, 'holiday_date': ['between', [start, end]]},
            fields=['holiday_date', 'description']
        ):
            holidays[str(h.holiday_date)] = h.description or 'Tatil'
    return holidays

@frappe.whitelist()
def update_work_order_date(work_order_id, new_start):
    try:
        from datetime import datetime, timedelta
        def to_8am(dt_str):
            return datetime.strptime(dt_str, "%Y-%m-%d").replace(hour=8, minute=0, second=0)

        work_order = frappe.get_doc("Work Order", work_order_id)
        old_start = work_order.planned_start_date
        old_end = work_order.planned_end_date
        # Eğer eski tarihlerden biri yoksa duration=0 kabul et
        if old_start and old_end:
            duration = (old_end - old_start).days
        else:
            duration = 0
        work_order.planned_start_date = to_8am(new_start)
        if duration > 0:
            new_end = to_8am(new_start) + timedelta(days=duration)
            work_order.planned_end_date = new_end
        else:
            work_order.planned_end_date = to_8am(new_start)
        work_order.save()
        # Operasyonları da yeni tarihe göre güncelle
        for op in work_order.operations:
            op.planned_start_time = work_order.planned_start_date
            if duration > 0:
                op.planned_end_time = work_order.planned_end_date
            else:
                op.planned_end_time = work_order.planned_start_date
        work_order.save()
        return {"success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Work Order Date Update Error")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_production_plan_chart_data(production_plan):
    """Get data for the production plan chart"""
    if not production_plan:
        return None

    # Get production plan details
    plan = frappe.get_doc('Production Plan', production_plan)
    
    # Example chart data structure
    # You can modify this according to your needs
    chart_data = {
        'labels': [],
        'datasets': [
            {
                'name': 'Planlanan Miktar',
                'values': []
            },
            {
                'name': 'Tamamlanan Miktar',
                'values': []
            }
        ]
    }

    # Get items from production plan
    for item in plan.po_items:
        chart_data['labels'].append(item.item_code)
        chart_data['datasets'][0]['values'].append(item.planned_qty)
        chart_data['datasets'][1]['values'].append(item.completed_qty or 0)

    return chart_data

@frappe.whitelist()
def get_daily_cutting_matrix(from_date, to_date):
    """
    Belirtilen tarih aralığındaki kesim planlarını getirir.
    """
    try:
        frappe.logger().info(f"[API] get_daily_cutting_matrix çağrıldı: from_date={from_date}, to_date={to_date}")
        # Tarihleri kontrol et ve formatla
        if not from_date or not to_date:
            frappe.logger().error("[API] Tarih parametreleri eksik")
            return []
        # Tarihleri YYYY-MM-DD formatına çevir
        try:
            from_date = frappe.utils.getdate(from_date).strftime('%Y-%m-%d')
            to_date = frappe.utils.getdate(to_date).strftime('%Y-%m-%d')
        except Exception as e:
            frappe.logger().error(f"[API] Tarih formatı hatası: {str(e)}")
            return []
        frappe.logger().info(f"[API] Formatlanmış tarihler: from_date={from_date}, to_date={to_date}")
        frappe.logger().info(f"[API] SQL sorgusu başlatılıyor: from_date={from_date}, to_date={to_date}")
        # SQL sorgusundan docstatus filtresi kaldırıldı
        result = frappe.db.sql("""
            SELECT 
                DATE(planning_date) AS date,
                workstation,
                SUM(total_mtul) AS total_mtul,
                SUM(total_quantity) AS total_quantity
            FROM `tabCutting Machine Plan`
            WHERE DATE(planning_date) BETWEEN %s AND %s
            GROUP BY DATE(planning_date), workstation
            ORDER BY DATE(planning_date), workstation
        """, (from_date, to_date), as_dict=True)
        frappe.logger().info(f"[API] SQL sorgusu tamamlandı. Kayıt sayısı: {len(result)}. Sonuç: {result}")
        if not result:
            # Veri yoksa örnek veri oluştur
            frappe.logger().info("[API] Sorgudan veri gelmedi, örnek veri oluşturuluyor.")
            current_date = frappe.utils.getdate(from_date)
            end_date = frappe.utils.getdate(to_date)
            result = []
            while current_date <= end_date:
                result.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'workstation': 'Kesim 1',
                    'total_mtul': 0,
                    'total_quantity': 0
                })
                current_date = frappe.utils.add_days(current_date, 1)
            frappe.logger().info(f"[API] Oluşturulan örnek veri: {result}")
        return result
    except Exception as e:
        frappe.logger().error(f"[API] get_daily_cutting_matrix hatası: {str(e)}")
        frappe.logger().error(frappe.get_traceback())
        return []

@frappe.whitelist()
def generate_cutting_plan(docname):
    """
    Verilen Production Plan belgesine bağlı po_items verilerine göre;
    - Aynı planlama tarihi ve iş istasyonu varsa o Cutting Machine Plan belgesine ekleme yapılır.
    - Yoksa yeni belge oluşturulur.
    - Her satır sadece bir kez eklenir.
    """
    doc = frappe.get_doc("Production Plan", docname)

    plan_map = {}  # key: date::workstation → Cutting Machine Plan nesnesi

    for row in doc.po_items:
        # Gerekli alanları al
        workstation_name = row.custom_workstation
        date_obj = row.planned_start_date
        mtul = row.custom_mtul_per_piece
        qty = row.planned_qty

        # Tarih objesini stringe çevir
        date = frappe.utils.getdate(date_obj).isoformat()

        # Zorunlu alan kontrolü
        if not (workstation_name and date and mtul and qty):
            continue

        key = f"{date}::{workstation_name}"

        # plan_map'te yoksa Cutting Plan bul/oluştur
        if key not in plan_map:
            existing_plan = frappe.db.get_value(
                "Cutting Machine Plan",
                filters={"planning_date": date, "workstation": workstation_name},
                fieldname="name"
            )

            if existing_plan:
                plan_doc = frappe.get_doc("Cutting Machine Plan", existing_plan)
            else:
                plan_doc = frappe.new_doc("Cutting Machine Plan")
                plan_doc.planning_date = date
                plan_doc.workstation = workstation_name
                plan_doc.insert(ignore_permissions=True)

            plan_map[key] = plan_doc
        else:
            plan_doc = plan_map[key]

        # Aynı üretim planı + satırı zaten varsa tekrar ekleme
        is_duplicate = any(
            d.production_plan == doc.name and d.production_plan_item == row.name
            for d in plan_doc.plan_details
        )
        if is_duplicate:
            continue

        # Yeni satırı ekle
        plan_doc.append("plan_details", {
            "item_code": row.item_code,
            "mtul_per_piece": mtul,
            "quantity": qty,
            "total_mtul": float(mtul) * float(qty),
            "production_plan": doc.name,
            "production_plan_item": row.name
        })

    # Belgeleri kaydet
    for plan_doc in plan_map.values():
        plan_doc.total_quantity = sum(d.quantity for d in plan_doc.plan_details)
        plan_doc.total_mtul = sum(d.total_mtul for d in plan_doc.plan_details)
        plan_doc.save(ignore_permissions=True)

    return {"success": True, "message": "Kesim Planı Başarıyla Oluşturuldu."}

@frappe.whitelist()
def delete_cutting_plans(docname):
    """
    Production Plan iptal edildiğinde ilgili kesim planlarını siler.
    """
    try:
        cutting_plans = frappe.get_all("Cutting Machine Plan", fields=["name"])
        for plan in cutting_plans:
            doc_plan = frappe.get_doc("Cutting Machine Plan", plan.name)
            original_len = len(doc_plan.plan_details)
            updated_rows = [d for d in doc_plan.plan_details if d.production_plan != docname]
        
            if len(updated_rows) != original_len:
                doc_plan.set("plan_details", updated_rows)
                if updated_rows:
                    doc_plan.total_quantity = sum(d.quantity for d in updated_rows)
                    doc_plan.total_mtul = sum(d.total_mtul for d in updated_rows)
                    doc_plan.save(ignore_permissions=True)
                else:
                    frappe.delete_doc("Cutting Machine Plan", doc_plan.name, force=True)
                    
        return {"success": True, "message": "Kesim Planları Otomatik Olarak Silindi"}

    except Exception as e:
        return {"success": False, "message": f"Kesim Planı Silinemedi: {str(e)}"}

@frappe.whitelist()
def get_profile_stock_panel(profil=None, depo=None, boy=None, scrap=None):
    """
    Profil stok paneli için birleşik ve filtrelenebilir veri seti döner.
    - ERPNext anlık stok (mtül)
    - Rezerv (mtül)
    - Kullanılabilir (mtül)
    - Boy bazında stok (adet, mtül)
    - Parça profil (is_scrap_piece)
    - Rezervasyon (boy/adet)
    - Son giriş/çıkış tarihi
    Filtreler: profil, depo, boy, scrap (opsiyonel)
    """
    frappe.log_error(
        title="STOK PANEL DEBUG",
        message=f"[DEBUG] get_profile_stock_panel params: profil={profil}, depo={depo}, boy={boy}, scrap={scrap}"
    )
    bin_filters = {}
    if profil: bin_filters["item_code"] = profil.strip()
    if depo: bin_filters["warehouse"] = depo.strip()
    bins = frappe.get_all("Bin", filters=bin_filters, fields=["item_code", "actual_qty", "reserved_qty", "warehouse"])
    frappe.log_error(
        title="STOK PANEL DEBUG",
        message=f"[DEBUG] bins count: {len(bins)}, örnek: {bins[0] if bins else 'yok'}"
    )
    ledger_filters = {}
    if profil: ledger_filters["profile_type"] = profil.strip()
    if boy is not None and boy != "":
        try:
            ledger_filters["length"] = float(boy)
        except:
            ledger_filters["length"] = boy
    if scrap is not None:
        ledger_filters["is_scrap_piece"] = int(scrap)
    ledgers = frappe.get_all(
        "Profile Stock Ledger",
        filters=ledger_filters,
        fields=["profile_type", "length", "qty", "total_length", "is_scrap_piece", "modified"]
    )
    frappe.log_error(
        title="STOK PANEL DEBUG",
        message=f"[DEBUG] ledgers count: {len(ledgers)}, örnek: {ledgers[0] if ledgers else 'yok'}"
    )
    # Rezervasyonlar (örnek: Profile Reservation doctype varsa)
    if frappe.db.table_exists("Profile Reservation"):
        reservations = frappe.get_all(
            "Profile Reservation",
            fields=["profile_type", "length", "reserved_qty"]
        )
    else:
        reservations = []
    last_dates = {}
    for l in ledgers:
        entry = frappe.get_all("Profile Entry Item", filters={"item_code": l["profile_type"], "length": l["length"]}, fields=["parent", "creation"], order_by="creation desc", limit=1)
        exit = frappe.get_all("Profile Exit Item", filters={"item_code": l["profile_type"], "length": l["length"]}, fields=["parent", "creation"], order_by="creation desc", limit=1)
        last_dates[l["profile_type"], l["length"]] = {
            "last_entry": entry[0]["creation"] if entry else None,
            "last_exit": exit[0]["creation"] if exit else None
        }
    # Profil adlarını topluca çek
    item_names = {}
    if ledgers:
        item_codes = list(set([l["profile_type"] for l in ledgers]))
        for item in frappe.get_all("Item", filters={"item_code": ["in", item_codes]}, fields=["item_code", "item_name"]):
            item_names[item["item_code"]] = item["item_name"]
    result = []
    for b in bins:
        for l in ledgers:
            # Eşleşme: profil ve boy birebir aynı olmalı, depo Bin'den alınacak
            if (
                str(l["profile_type"]).strip().lower() == str(b["item_code"]).strip().lower() and
                (boy is None or str(l["length"]) == str(boy) or (isinstance(boy, (int, float)) and float(l["length"]) == float(boy)))
            ):
                rezerv = next((r for r in reservations if r["profile_type"] == l["profile_type"] and r["length"] == l["length"]), None)
                tarih = last_dates.get((l["profile_type"], l["length"]), {})
                result.append({
                    "profil": b["item_code"],
                    "profil_adi": item_names.get(b["item_code"], ""),
                    "depo": b["warehouse"],
                    "erpnext_stok": b["actual_qty"],
                    "rezerv": b["reserved_qty"],
                    "kullanilabilir": b["actual_qty"] - b["reserved_qty"],
                    "boy": l["length"],
                    "boy_stok_adet": l["qty"],
                    "boy_stok_mtul": l["total_length"],
                    "scrap": l["is_scrap_piece"] if "is_scrap_piece" in l else 0,
                    "boy_rezerv": rezerv["reserved_qty"] if rezerv else 0,
                    "son_giris": tarih.get("last_entry"),
                    "son_cikis": tarih.get("last_exit"),
                    "guncelleme": l["modified"]
                })
    frappe.log_error(
        title="STOK PANEL DEBUG",
        message=f"[DEBUG] result length: {len(result)}"
    )
    return result

@frappe.whitelist()
def get_total_stock_summary(profil=None, depo=None):
    """
    ERPNext Bin tablosundan toplam stok (mtül) bilgisini depo ve ürün bazında döndürür.
    Ayrıca, Rezerved Raw Materials doctype'ından toplam rezerv (mtül) ve kullanılabilir (mtül) değerlerini de ekler.
    """
    filters = {}
    if profil:
        filters["item_code"] = profil
    if depo:
        filters["warehouse"] = depo
    bins = frappe.get_all("Bin", filters=filters, fields=["item_code", "warehouse", "actual_qty"])
    # item_name ekle
    item_names = {}
    if bins:
        item_codes = list(set([b["item_code"] for b in bins]))
        for item in frappe.get_all("Item", filters={"item_code": ["in", item_codes]}, fields=["item_code", "item_name"]):
            item_names[item["item_code"]] = item["item_name"]
    # Rezervleri çek (mtül bazında)
    rezervler = frappe.get_all(
        "Rezerved Raw Materials",
        fields=["item_code", "quantity"],
        filters={"item_code": ["in", [b["item_code"] for b in bins]]} if bins else {}
    )
    rezerv_map = {}
    for r in rezervler:
        rezerv_map.setdefault(r["item_code"], 0)
        rezerv_map[r["item_code"]] += float(r["quantity"] or 0)
    result = []
    for b in bins:
        rezerv_mtul = rezerv_map.get(b["item_code"], 0)
        kullanilabilir_mtul = float(b["actual_qty"] or 0) - rezerv_mtul
        result.append({
            "profil": b["item_code"],
            "profil_adi": item_names.get(b["item_code"], ""),
            "depo": b["warehouse"],
            "toplam_stok_mtul": b["actual_qty"],
            "rezerv_mtul": rezerv_mtul,
            "kullanilabilir_mtul": kullanilabilir_mtul
        })
    return result 

@frappe.whitelist()
def get_materials_by_opti(opti_no):
    """
    Girdi: Production Plan'ın name (docname) değeri
    Çıktı: Üretim planı, bağlı satış siparişleri, malzeme listesi (MLY entegrasyonu için placeholder)
    """
    plan = frappe.get_doc("Production Plan", opti_no)
    if not plan:
        frappe.throw(_("Production Plan not found for OpTi No: {0}").format(opti_no))
    # Child table'dan sales_orders listesini çek
    sales_orders = [row.sales_order for row in plan.sales_orders if row.sales_order]
    # Placeholder: Fetch MLY file materials (to be implemented)
    materials = []  # Bu kısım API ile doldurulacak
    return {
        "production_plan": plan.name,
        "sales_orders": sales_orders,
        "materials": materials
    }

# --- Accessory Delivery Package API ---

@frappe.whitelist()
def get_approved_opti_nos():
    """
    Onaylı üretim planlarının hem OpTi No (opti_no) hem de name (docname) değerlerini döndürür.
    """
    return frappe.get_all(
        "Production Plan",
        filters={"docstatus": 1},
        fields=["name", "opti_no"],
        order_by="creation desc"
    )

@frappe.whitelist()
def get_sales_orders_by_opti(opti_no):
    """
    Seçilen OpTi No'ya (Production Plan'ın name'i) ait satış siparişlerini, sales_orders child table'ından döndürür.
    """
    plan = frappe.get_doc("Production Plan", opti_no)
    if not plan:
        return []
    sales_orders = [row.sales_order for row in plan.sales_orders if row.sales_order]
    return sales_orders

@frappe.whitelist()
def get_bom_materials_by_sales_order(sales_order):
    """
    Verilen satış siparişine (sales_order) ait Work Order'lardan veya doğrudan Sales Order/BOM'dan ilgili BOM item'larını döndürür.
    Zincir:
    1. Onaylı Work Order → BOM → BOM Item
    2. Onaysız Work Order → BOM → BOM Item
    3. Sales Order'ın bom_no'su → BOM Item
    4. Production Plan üzerinden BOM bul (varsa)
    """
    import frappe
    items = []
    frappe.log_error(f"[DEBUG] get_bom_materials_by_sales_order sales_order={sales_order}")
    # 1. Onaylı Work Order
    work_orders = frappe.get_all(
        "Work Order",
        filters={"sales_order": sales_order, "docstatus": 1},
        fields=["name", "bom_no", "qty"]
    )
    if not work_orders:
        # 2. Onaysız Work Order
        work_orders = frappe.get_all(
            "Work Order",
            filters={"sales_order": sales_order},
            fields=["name", "bom_no", "qty"]
        )
        frappe.log_error(f"[DEBUG] Onaysız Work Order arandı, bulunan: {work_orders}")
    else:
        frappe.log_error(f"[DEBUG] Onaylı Work Order bulundu: {work_orders}")
    for wo in work_orders:
        if not wo.bom_no:
            continue
        bom_items = frappe.get_all(
            "BOM Item",
            filters={"parent": wo.bom_no},
            fields=["item_code", "item_name", "qty", "uom"]
        )
        for item in bom_items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "uom": item.uom
            })
    if items:
        frappe.log_error(f"[DEBUG] Work Order zincirinden malzeme bulundu, count={len(items)}")
        return items
    # 3. Sales Order'ın bom_no'su
    so = frappe.get_value("Sales Order", sales_order, ["bom_no"])
    if so and so[0]:
        bom_no = so[0]
        bom_items = frappe.get_all(
            "BOM Item",
            filters={"parent": bom_no},
            fields=["item_code", "item_name", "qty", "uom"]
        )
        for item in bom_items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "uom": item.uom
            })
        if items:
            frappe.log_error(f"[DEBUG] Sales Order'ın bom_no'sundan malzeme bulundu, count={len(items)}")
            return items
    # 4. Production Plan üzerinden BOM bul
    plan_name = frappe.db.get_value("Production Plan Sales Order", {"sales_order": sales_order}, "parent")
    if plan_name:
        plan = frappe.get_doc("Production Plan", plan_name)
        for row in getattr(plan, "po_items", []):
            if getattr(row, "sales_order", None) == sales_order and getattr(row, "bom_no", None):
                bom_items = frappe.get_all(
                    "BOM Item",
                    filters={"parent": row.bom_no},
                    fields=["item_code", "item_name", "qty", "uom"]
                )
                for item in bom_items:
                    items.append({
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "qty": item.qty,
                        "uom": item.uom
                    })
        if items:
            frappe.log_error(f"[DEBUG] Production Plan zincirinden malzeme bulundu, count={len(items)}")
            return items
    frappe.log_error(f"[DEBUG] Hiçbir zincirden malzeme bulunamadı.")
    return items

@frappe.whitelist()
def create_delivery_package(data):
    """
    Verilen bilgilerle Accessory Delivery Package oluşturur (malzeme listesi, opti_no, teslim alan, notlar, vb).
    """
    import json
    if isinstance(data, str):
        data = json.loads(data)
    doc = frappe.new_doc("Accessory Delivery Package")
    doc.opti_no = data.get("opti_no")
    doc.sales_order = data.get("sales_order")
    doc.delivered_to = data.get("delivered_to")
    doc.delivered_by = frappe.session.user
    doc.delivery_date = frappe.utils.now_datetime()
    doc.notes = data.get("notes")
    for item in data.get("item_list", []):
        doc.append("item_list", {
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "qty": item.get("qty"),
            "uom": item.get("uom")
        })
    doc.save()
    frappe.db.commit()
    return {"name": doc.name} 
