import frappe
from frappe.utils import getdate, add_days, get_datetime
from datetime import timedelta
from calendar import monthrange
import pandas as pd

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

    schedule = []

    for ws in workstations:
        operation_filters = {
            'workstation': ws.name,
            'planned_start_time': ['between', [str(start_date), f"{str(end_date)} 23:59:59"]]
        }
        if status:
            operation_filters['status'] = status

        operations = frappe.get_all('Work Order Operation',
            filters=operation_filters,
            fields=[
                'name', 'parent as work_order', 'operation', 'workstation',
                'planned_start_time', 'planned_end_time', 'status',
                'actual_start_time', 'actual_end_time', 'time_in_mins',
                'completed_qty'
            ]
        )

        # Çalışma saatlerini child table'dan çek
        ws_doc = frappe.get_doc('Workstation', ws.name)
        work_hours = []
        for row in getattr(ws_doc, 'working_hours', []):
            if getattr(row, 'enabled', 1):
                work_hours.append({
                    'start_time': row.start_time,
                    'end_time': row.end_time
                })
        # Her gün için toplam dakika
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
        # Günlük özetler için
        daily_summary = {}
        if work_hours:
            for i in range(7):
                total = 0
                for wh in work_hours:
                    start = wh['start_time']
                    end = wh['end_time']
                    from datetime import datetime
                    s = datetime.strptime(str(start), '%H:%M:%S') if ':' in str(start) else datetime.strptime(str(start), '%H:%M')
                    e = datetime.strptime(str(end), '%H:%M:%S') if ':' in str(end) else datetime.strptime(str(end), '%H:%M')
                    diff = (e-s).seconds // 60
                    total += diff
                daily_work_minutes[i] = total
        else:
            for i in range(7):
                daily_work_minutes[i] = 0

        for op in operations:
            ops_in_this_week.add(op.operation)
            work_order = frappe.get_doc('Work Order', op.work_order)
            job_card = frappe.get_all('Job Card',
                filters={'work_order': op.work_order, 'operation': op.operation},
                fields=['name', 'for_quantity', 'status'],
                limit=1
            )

            op_status = ''
            if job_card and job_card[0].status:
                op_status = job_card[0].status
            elif op.completed_qty > 0:
                op_status = 'Devam Ediyor'
            elif op.actual_start_time:
                op_status = 'Başladı'

            start_dt = get_datetime(op.planned_start_time)
            end_dt = get_datetime(op.planned_end_time)
            # Planlanan süreyi dakika olarak hesapla
            time_in_mins = int((end_dt - start_dt).total_seconds() // 60) if start_dt and end_dt else 0
            total_hours += time_in_mins / 60
            total_operations += 1

            # Günlük planlanan dakika
            daily_summary.setdefault(day_name_tr[start_dt.strftime('%A')], {'planned_minutes': 0, 'jobs': 0})
            daily_summary[day_name_tr[start_dt.strftime('%A')]]['planned_minutes'] += time_in_mins
            daily_summary[day_name_tr[start_dt.strftime('%A')]]['jobs'] += 1

            day_schedule.setdefault(day_name_tr[start_dt.strftime('%A')], []).append({
                'name': job_card[0].name if job_card else "",
                'status': job_card[0].status if job_card and job_card[0].status else status_map.get(op.status or "", "Tanımsız"),
                'qty_to_manufacture': job_card[0].for_quantity if job_card else 0,
                'total_completed_qty': work_order.produced_qty,
                'item_name': work_order.item_name or '',
                'production_item': work_order.production_item or '',
                'bom_no': work_order.bom_no or '',
                'sales_order': work_order.sales_order or '',
                'work_order': op.work_order,
                'operation': op.operation or 'Operasyon Yok',
                'color': get_color_for_sales_order(work_order.sales_order),
                'start_time': start_dt.strftime('%Y-%m-%d %H:%M'),
                'end_time': end_dt.strftime('%Y-%m-%d %H:%M'),
                'expected_start_date': op.planned_start_time,
                'expected_end_date': op.planned_end_time,
                'actual_start_date': op.actual_start_time,
                'actual_end_date': op.actual_end_time,
                'total_time_in_mins': int((end_dt - start_dt).total_seconds() // 60),
                'time': f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}",
                'employee': "",
                'duration': time_in_mins,
                'op_status': op_status
            })


        # Günlük özetleri ekle
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
    holidays = get_holidays(start_date, end_date)
    holiday_map = {h['date']: h['reason'] for h in holidays}

    days = []
    for d in week_dates:
        iso = d.strftime('%Y-%m-%d')
        weekday = day_name_tr[d.strftime('%A')]
        is_weekend = d.weekday() >= 5  # Cumartesi, Pazar
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
    ])
    for op in op_children:
        # Zaman aralığı
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
            'status': op.get('status', ''),
            'completed_qty': op.get('completed_qty', ''),
            'planned_start_time': op.get('planned_start_time', ''),
            'planned_end_time': op.get('planned_end_time', ''),
            'time': time_str,
            'actual_start_time': op.get('actual_start_time', ''),
            'actual_end_time': op.get('actual_end_time', ''),
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
