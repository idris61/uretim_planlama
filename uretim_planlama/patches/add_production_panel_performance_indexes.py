# -*- coding: utf-8 -*-
# Copyright (c) 2025, idris and contributors
# For license information, please see license.txt

"""
Üretim Planlama Paneli Performance İndeksleri
Bu patch kritik performans artışı sağlayacak indeksleri ekler.
Tablolardaki yavaşlığın ana nedeni eksik indekslerdir.
"""

import frappe

def execute():
    """
    Üretim paneli için kritik performans indekslerini ekle
    """
    try:
        # İndeks listesi - Sorgu analizi sonucu belirlenen kritik indeksler
        indexes = [
            # Production Plan indeksleri
            {
                'table': 'tabProduction Plan',
                'name': 'idx_pp_opti_docstatus',
                'columns': ['custom_opti_no', 'docstatus', 'status'],
                'description': 'Opti numarası ve durum filtreleri için'
            },
            {
                'table': 'tabProduction Plan',
                'name': 'idx_pp_docstatus_status',
                'columns': ['docstatus', 'status'],
                'description': 'Temel durum filtreleri için'
            },
            
            # Production Plan Item indeksleri
            {
                'table': 'tabProduction Plan Item',
                'name': 'idx_ppi_parent_sales_order',
                'columns': ['parent', 'sales_order', 'planned_qty'],
                'description': 'JOIN ve miktar filtreleri için'
            },
            {
                'table': 'tabProduction Plan Item',
                'name': 'idx_ppi_sales_order_item',
                'columns': ['sales_order_item', 'planned_qty'],
                'description': 'Planlanmamış hesaplama için'
            },
            {
                'table': 'tabProduction Plan Item',
                'name': 'idx_ppi_planned_start_date',
                'columns': ['planned_start_date'],
                'description': 'Tarih filtreleri için'
            },
            
            # Sales Order indeksleri
            {
                'table': 'tabSales Order',
                'name': 'idx_so_docstatus_delivery',
                'columns': ['docstatus', 'delivery_date', 'customer'],
                'description': 'Temel sipariş filtreleri için'
            },
            {
                'table': 'tabSales Order',
                'name': 'idx_so_transaction_date',
                'columns': ['transaction_date'],
                'description': 'Hafta hesaplama için'
            },
            {
                'table': 'tabSales Order',
                'name': 'idx_so_workflow_state',
                'columns': ['workflow_state', 'docstatus'],
                'description': 'İş akışı filtreleri için'
            },
            
            # Sales Order Item indeksleri
            {
                'table': 'tabSales Order Item',
                'name': 'idx_soi_parent_item_qty',
                'columns': ['parent', 'item_code', 'qty'],
                'description': 'Sipariş item JOIN ve miktar için'
            },
            
            # Item indeksleri
            {
                'table': 'tabItem',
                'name': 'idx_item_group_stok_turu',
                'columns': ['item_group', 'custom_stok_türü'],
                'description': 'Ürün grubu filtreleri için'
            },
            {
                'table': 'tabItem',
                'name': 'idx_item_serial_color',
                'columns': ['custom_serial', 'custom_color'],
                'description': 'Seri ve renk filtreleri için'
            },
            
            # Work Order indeksleri
            {
                'table': 'tabWork Order',
                'name': 'idx_wo_production_plan_status',
                'columns': ['production_plan', 'docstatus', 'status'],
                'description': 'İş emri istatistikleri için'
            },
            {
                'table': 'tabWork Order',
                'name': 'idx_wo_sales_order',
                'columns': ['sales_order', 'docstatus'],
                'description': 'Sipariş bazlı iş emirleri için'
            }
        ]
        
        # İndeksleri oluştur
        created_count = 0
        skipped_count = 0
        
        for index_config in indexes:
            try:
                table_name = index_config['table']
                index_name = index_config['name']
                columns = index_config['columns']
                description = index_config['description']
                
                # İndeks zaten var mı kontrol et
                existing_indexes = frappe.db.sql(f"""
                    SHOW INDEX FROM `{table_name}` 
                    WHERE Key_name = %s
                """, index_name)
                
                if existing_indexes:
                    frappe.logger().info(f"İndeks zaten mevcut: {index_name}")
                    skipped_count += 1
                    continue
                
                # İndeksi oluştur
                columns_str = ', '.join([f"`{col}`" for col in columns])
                create_index_sql = f"""
                    CREATE INDEX `{index_name}` 
                    ON `{table_name}` ({columns_str})
                """
                
                frappe.db.sql(create_index_sql)
                frappe.logger().info(f"İndeks oluşturuldu: {index_name} - {description}")
                created_count += 1
                
            except Exception as e:
                frappe.logger().error(f"İndeks oluşturma hatası ({index_name}): {str(e)}")
                continue
        
        # Commit işlemi
        frappe.db.commit()
        
        # Sonuç mesajı
        message = f"Performance indeksleri eklendi: {created_count} yeni, {skipped_count} mevcut"
        frappe.logger().info(message)
        print(message)
        
        return {
            'success': True,
            'created': created_count,
            'skipped': skipped_count,
            'message': message
        }
        
    except Exception as e:
        frappe.logger().error(f"İndeks patch hatası: {str(e)}")
        frappe.db.rollback()
        return {
            'success': False,
            'error': str(e)
        }

