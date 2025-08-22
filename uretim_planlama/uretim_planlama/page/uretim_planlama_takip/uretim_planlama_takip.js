// Üretim Planlama Takip Paneli - Frappe JS Framework
// Sadece Planlanan Siparişler - Modern Tasarım



// CSS Stilleri - Modern ve Optimize
const styles = `
<style>
/* Modern Renk Kodlaması */
.pvc-row { background-color: #fff8dc !important; border-left: 4px solid #ffc107 !important; }
.cam-row { background-color: #e3f2fd !important; border-left: 4px solid #17a2b8 !important; }
.mixed-row { background-color: #f8d7da !important; border-left: 4px solid #dc3545 !important; }

.urgent-delivery { background-color: #ffebee !important; border-left: 4px solid #f44336 !important; }

/* Modern Tablo Tasarımı */
.table-container { 
    position: relative; 
    max-height: 600px; 
    overflow-y: auto; 
    overflow-x: hidden; 
    border: 2px solid #adb5bd; 
    border-radius: 12px; 
    box-shadow: 0 8px 25px rgba(0,0,0,0.15); 
    width: 100%; 
    min-width: 100%; 
    background: white;
}

/* Scroll Bar Stilleri */
.table-container::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

.table-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 6px;
}

.table-container::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 6px;
    border: 2px solid #f1f1f1;
}

.table-container::-webkit-scrollbar-thumb:hover {
    background: #555;
}

.table-container::-webkit-scrollbar-corner {
    background: #f1f1f1;
}

.table-container table { 
    margin-bottom: 0; 
    width: 100%; 
    min-width: 100%; 
    table-layout: fixed; 
    border-collapse: separate;
    border-spacing: 0;
}

.table-container thead th { 
    position: sticky; 
    top: 0; 
    z-index: 10; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    color: white; 
    font-weight: 600; 
    text-transform: uppercase; 
    font-size: 0.8rem; 
    letter-spacing: 0.2px; 
    border-right: 1px solid #5a6fd8; 
    border-left: 1px solid #5a6fd8; 
    padding: 6px 3px; 
    text-align: center; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
    white-space: nowrap; 
    height: 32px; 
    overflow: hidden; 
    text-overflow: ellipsis; 
}

.table-container thead th:first-child { border-top-left-radius: 12px; }
.table-container thead th:last-child { border-top-right-radius: 12px; }

/* Profesyonel Tablo Renklendirme */
.table-container tbody tr { 
    transition: all 0.3s ease; 
    height: 4rem !important; 
    min-height: 4rem !important; 
    max-height: 4rem !important; 
    margin-bottom: 2px !important; 
    border-bottom: 1px solid #dee2e6 !important; 
    border-top: 1px solid #dee2e6 !important; 
}

.table-container tbody td { 
    padding: 6px 4px !important; 
    font-size: 0.9rem !important; 
    font-weight: bold !important; 
    line-height: 1.2 !important; 
    max-height: 4rem !important; 
    overflow: hidden !important; 
    text-overflow: ellipsis !important; 
    white-space: nowrap !important; 
    vertical-align: middle !important; 
}

/* Tamamlanan Siparişler - En Yüksek Öncelik */
.table-container tbody tr.completed-row, 
.table-container tbody tr.completed-row:nth-child(even), 
.table-container tbody tr.completed-row:nth-child(odd) { 
    background-color: #00ff00 !important; 
    border-left: 4px solid #00cc00 !important; 
    color: #000000 !important; 
    font-weight: bold !important; 
}

.table-container tbody tr.completed-row:hover { 
    background: linear-gradient(135deg, #00ff00 0%, #00cc00 100%) !important; 
    transform: translateY(-1px); 
    box-shadow: 0 4px 8px rgba(0, 255, 0, 0.3); 
}

/* Tamamlanan satırlar için diğer renkleri geçersiz kıl */
.table-container tbody tr.completed-row.pvc-row,
.table-container tbody tr.completed-row.cam-row,
.table-container tbody tr.completed-row.mixed-row { 
    background-color: #00ff00 !important; 
    border-left: 4px solid #00cc00 !important; 
    color: #000000 !important; 
}

/* Alternatif satır renklendirmesi - Tamamlananları hariç tut */
.table-container tbody tr:nth-child(even):not(.pvc-row):not(.cam-row):not(.mixed-row):not(.completed-row) { 
    background-color: #f8f9fa !important; 
}

.table-container tbody tr:nth-child(odd):not(.pvc-row):not(.cam-row):not(.mixed-row):not(.completed-row) { 
    background-color: #ffffff !important; 
}



.table-container tbody tr.pvc-row, 
.table-container tbody tr.pvc-row:nth-child(even), 
.table-container tbody tr.pvc-row:nth-child(odd) { 
    background-color: #fff8dc !important; 
    border-left: 4px solid #ffc107 !important; 
}

.table-container tbody tr.pvc-row:hover { 
    background: linear-gradient(135deg, #fff8dc 0%, #ffeaa7 100%) !important; 
    transform: translateY(-1px); 
    box-shadow: 0 4px 8px rgba(255, 193, 7, 0.2); 
}

.table-container tbody tr.cam-row, 
.table-container tbody tr.cam-row:nth-child(even), 
.table-container tbody tr.cam-row:nth-child(odd) { 
    background-color: #e3f2fd !important; 
    border-left: 4px solid #17a2b8 !important; 
}

.table-container tbody tr.cam-row:hover { 
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important; 
    transform: translateY(-1px); 
    box-shadow: 0 4px 8px rgba(23, 162, 184, 0.2); 
}

.table-container tbody tr.mixed-row, 
.table-container tbody tr.mixed-row:nth-child(even), 
.table-container tbody tr.mixed-row:nth-child(odd) { 
    background-color: #f8d7da !important; 
    border-left: 4px solid #dc3545 !important; 
}

.table-container tbody tr.mixed-row:hover { 
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important; 
    transform: translateY(-1px); 
    box-shadow: 0 4px 8px rgba(220, 53, 69, 0.2); 
}

/* Sipariş Satırları */
.table-container tbody tr.order-row {
    border-left: 2px solid #dee2e6 !important;
    background-color: rgba(255, 255, 255, 0.8) !important;
    cursor: pointer;
}

.table-container tbody tr.order-row:hover {
    background-color: rgba(255, 255, 255, 0.95) !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Modal Stilleri */
.modal-xl {
    max-width: 80%;
}

.modal-header {
    border-radius: 0.5rem 0.5rem 0 0;
    padding: 1rem 1.5rem;
}

.modal-body {
    border-radius: 0;
}

.modal-footer {
    border-radius: 0 0 0.5rem 0.5rem;
    padding: 1rem 1.5rem;
}

/* Modal Tablo Stilleri */
.modal .table {
    margin-bottom: 0;
}

.modal .table th {
    border-top: none;
    font-weight: bold;
    padding: 0.75rem 0.5rem;
}

.modal .table td {
    padding: 0.5rem;
    vertical-align: middle;
    white-space: normal;
    word-break: break-word;
    line-height: 1.2;
}

.modal .card {
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.modal .card-header {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: bold;
    padding: 0.75rem 1rem;
}

.modal .alert {
    margin: 1rem;
    border-radius: 0.5rem;
}

/* İş Emirleri Modal Stilleri */
.modal .card {
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}

.modal .card:last-child {
    margin-bottom: 0;
}

.modal .card-header {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: bold;
    padding: 0.75rem 1rem;
}

.modal .table th {
    border-top: none;
    font-weight: bold;
    padding: 0.75rem 0.5rem;
    font-size: 0.85rem;
}

.modal .table td {
    padding: 0.5rem;
    vertical-align: middle;
    font-size: 0.8rem;
}

.modal .badge {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
}

.modal .btn-sm {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
}

/* Tıklanabilir Toggle Stilleri */
.clickable-toggle {
    transition: all 0.3s ease;
    border-radius: 4px;
    padding: 4px 8px;
}

.clickable-toggle:hover {
    background-color: rgba(255, 255, 255, 0.1);
    transform: translateY(-1px);
}

.clickable-toggle:active {
    transform: translateY(0);
    background-color: rgba(255, 255, 255, 0.2);
}

.clickable-toggle.disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.table-container tbody tr:hover { 
    background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); 
    transform: translateY(-1px); 
    box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
}

.table-container tbody td { 
    padding: 4px 6px; 
    vertical-align: middle; 
    border-right: 1px solid #dee2e6; 
    border-left: 1px solid #dee2e6; 
    font-size: 0.75rem; 
    text-align: center; 
    line-height: 1.1; 
    max-height: 3.5rem; 
    overflow: hidden; 
    word-wrap: break-word; 
    white-space: normal; 
    text-overflow: ellipsis; 
    max-width: 0; 
}

/* Opti başlık satırları için özel stil */
.table-container tbody tr.opti-header-row td {
    padding: 6px 8px;
    font-size: 0.8rem;
    font-weight: bold;
}

/* Sipariş satırları için özel stil */
.table-container tbody tr.order-row td {
    padding: 4px 6px;
    font-size: 0.7rem;
}

/* Badge Stilleri - Modern */
.badge { 
    font-weight: bold; 
    margin: 1px; 
    display: inline-block; 
    font-size: 0.75rem; 
    border-radius: 4px; 
    padding: 3px 5px; 
    border: 1px solid; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}



/* Modern Card Stilleri */
.card { 
    border: none; 
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.1); 
    border-radius: 16px; 
    margin-bottom: 2rem; 
    overflow: hidden; 
    transition: all 0.3s ease; 
}

.card:hover { 
    transform: translateY(-3px); 
    box-shadow: 0 15px 45px rgba(0,0,0,0.15); 
}

.card-header { 
    border-radius: 16px 16px 0 0 !important; 
    font-weight: 700; 
    font-size: 1.2rem; 
    padding: 20px 25px; 
    border-bottom: 2px solid rgba(0,0,0,0.1); 
}

/* Modern Button Stilleri */
.btn { 
    border-radius: 10px; 
    padding: 12px 24px; 
    font-weight: 600; 
    text-transform: uppercase; 
    letter-spacing: 0.5px; 
    transition: all 0.3s ease; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
}

.btn:hover { 
    transform: translateY(-2px); 
    box-shadow: 0 6px 20px rgba(0,0,0,0.2); 
}

.btn-primary { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    border: none; 
}

.btn-secondary { 
    background: linear-gradient(135deg, #adb5bd 0%, #868e96 100%); 
    border: none; 
}

.btn-sm { 
    padding: 6px 12px; 
    font-size: 0.8rem; 
    border-radius: 8px; 
}

/* Modern Form Stilleri */
.form-control { 
    border-radius: 10px; 
    border: 2px solid #e9ecef; 
    padding: 12px 16px; 
    transition: all 0.3s ease; 
    font-size: 0.9rem;
}

.form-control:focus { 
    border-color: #667eea; 
    box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25); 
}

/* Modern Filtre Stilleri */
.filter-section {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 16px;
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.filter-row {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: end;
}

.filter-group {
    flex: 1;
    min-width: 200px;
}

.filter-group label {
    font-weight: 600;
    color: #495057;
    margin-bottom: 8px;
    display: block;
}

/* Tek Satır Filtre Stilleri */
.filter-single-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: nowrap;
    padding: 8px 0;
    width: 100%;
}

.filter-inputs {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    flex-wrap: nowrap;
    width: 100%;
}

.filter-input-item {
    flex: 1;
    min-width: 0;
}

.filter-input-item:nth-child(1) { flex: 0.8; }  /* Opti No */
.filter-input-item:nth-child(2) { flex: 1.2; }  /* Sipariş No */
.filter-input-item:nth-child(3) { flex: 1.0; }  /* Bayi */
.filter-input-item:nth-child(4) { flex: 1.2; }  /* Müşteri */
.filter-input-item:nth-child(5) { flex: 1.0; }  /* Seri */
.filter-input-item:nth-child(6) { flex: 0.8; }  /* Renk */
.filter-input-item:nth-child(7) { flex: 0.8; }  /* Durum */
.filter-input-item:nth-child(8) { flex: 0.6; }  /* Temizle */

.filter-input-item input,
.filter-input-item select {
    border-radius: 6px;
    font-size: 0.65rem;
    border: 1px solid #ced4da;
    transition: all 0.3s ease;
    padding: 0.2rem 0.4rem;
    height: 30px;
    width: 100%;
    min-width: 0;
}

.filter-input-item input:focus,
.filter-input-item select:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.filter-input-item button {
    font-size: 0.65rem;
    padding: 0.2rem 0.4rem;
    height: 30px;
    white-space: nowrap;
    width: 100%;
}

/* Header Stilleri */
.header-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Özet Kartları Stilleri */
.summary-card {
    transition: all 0.3s ease;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.summary-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.summary-card .card-body {
    padding: 15px;
}

.summary-card i {
    opacity: 0.9;
}

/* Modern Modal Stilleri */
.modal .modal-header { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    color: white; 
    border-bottom: none; 
    border-radius: 16px 16px 0 0; 
    padding: 20px 25px;
}

.modal .modal-footer { 
    background-color: #f8f9fa; 
    border-top: 2px solid #dee2e6; 
    border-radius: 0 0 16px 16px; 
    padding: 20px 25px;
}



/* Buton Grupları Stilleri */
.btn-group .btn {
    border-radius: 0;
    margin: 0;
    padding: 2px 6px;
    font-size: 0.7rem;
}

.btn-group .btn:first-child {
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

.btn-group .btn:last-child {
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}

.btn-xs {
    padding: 2px 6px;
    font-size: 0.7rem;
    line-height: 1.2;
}

/* Responsive Tasarım */
@media (max-width: 768px) {
    .table-container { font-size: 12px; }
    
    .card-header { font-size: 1rem; padding: 15px 20px; }
    
    /* Mobil filtre düzeni */
    .filter-single-row {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
        padding: 8px 0;
    }
    
    .filter-inputs {
        flex-direction: column;
        gap: 8px;
        width: 100%;
    }
    
    .filter-input-item {
        width: 100%;
        flex: none;
    }
    
    .filter-input-item input,
    .filter-input-item select,
    .filter-input-item button {
        height: 36px;
        font-size: 0.8rem;
        width: 100%;
    }
}

@media (max-width: 1200px) {
    .filter-input-item:nth-child(1) { flex: 0.7; }  /* Opti No */
    .filter-input-item:nth-child(2) { flex: 1.0; }  /* Sipariş No */
    .filter-input-item:nth-child(3) { flex: 0.8; }  /* Bayi */
    .filter-input-item:nth-child(4) { flex: 1.0; }  /* Müşteri */
    .filter-input-item:nth-child(5) { flex: 0.8; }  /* Seri */
    .filter-input-item:nth-child(6) { flex: 0.7; }  /* Renk */
    .filter-input-item:nth-child(7) { flex: 0.7; }  /* Durum */
    .filter-input-item:nth-child(8) { flex: 0.5; }  /* Temizle */
    
    .filter-input-item input,
    .filter-input-item select,
    .filter-input-item button {
        font-size: 0.6rem;
        padding: 0.15rem 0.3rem;
        height: 28px;
    }
}

@media (min-width: 1400px) {
    .filter-input-item:nth-child(1) { flex: 0.9; }  /* Opti No */
    .filter-input-item:nth-child(2) { flex: 1.4; }  /* Sipariş No */
    .filter-input-item:nth-child(3) { flex: 1.2; }  /* Bayi */
    .filter-input-item:nth-child(4) { flex: 1.4; }  /* Müşteri */
    .filter-input-item:nth-child(5) { flex: 1.2; }  /* Seri */
    .filter-input-item:nth-child(6) { flex: 0.9; }  /* Renk */
    .filter-input-item:nth-child(7) { flex: 0.9; }  /* Durum */
    .filter-input-item:nth-child(8) { flex: 0.7; }  /* Temizle */
    
    .filter-input-item input,
    .filter-input-item select,
    .filter-input-item button {
        font-size: 0.7rem;
        padding: 0.25rem 0.5rem;
        height: 32px;
    }
}

/* Performans Optimizasyonları */
.table th, .table td { 
    white-space: normal; 
    overflow: hidden; 
    text-overflow: ellipsis; 
    max-width: 200px; 
    vertical-align: middle; 
    word-wrap: break-word; 
}

/* Scroll Bar Stilleri */
.table-container::-webkit-scrollbar { 
    width: 12px; 
    height: 12px; 
}

.table-container::-webkit-scrollbar-track { 
    background: #f8f9fa; 
    border-radius: 6px; 
    border: 1px solid #e9ecef; 
}

.table-container::-webkit-scrollbar-thumb { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
    border-radius: 6px; 
    border: 1px solid rgba(255,255,255,0.2); 
}

.table-container::-webkit-scrollbar-thumb:hover { 
    background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%); 
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4); 
}

.table-container { 
    scrollbar-width: thin; 
    scrollbar-color: #667eea #f8f9fa; 
}
</style>
`;

// Frappe sayfa yapısı
frappe.pages['uretim_planlama_takip'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Üretim Planlama Takip Paneli',
        single_column: true
    });
    
    // CSS stillerini ekle
    if (!document.getElementById('uretim-takip-styles')) {
        const styleElement = document.createElement('div');
        styleElement.id = 'uretim-takip-styles';
        styleElement.innerHTML = styles;
        document.head.appendChild(styleElement);
    }
    
    // Ana container oluştur
    let container = $('<div class="container-fluid"></div>').appendTo(page.body);
    
    // Sayfa yapısını oluştur
    createPageStructure(container);
    bindEvents();
    loadProductionData();
    startAutoUpdate();
};

// Utility functions - Performance optimized
const utils = {
    // Güvenli HTML escape
    escapeHtml: (text) => {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Format date safely - Cached for performance
    formatDate: (() => {
        const cache = new Map();
        return (dateStr) => {
            if (!dateStr || dateStr === '-' || dateStr === 'None' || dateStr === '') return '-';
            const str = String(dateStr);
            if (cache.has(str)) return cache.get(str);

            // Eğer zaten dd.mm.yyyy formatındaysa, olduğu gibi göster
            const dmyRegex = /^\d{2}\.\d{2}\.\d{4}$/;
            if (dmyRegex.test(str)) {
                cache.set(str, str);
                return str;
            }

            try {
                // ISO veya parse edilebilir formatlar
                // ISO'yu (yyyy-mm-dd) öncelikli parse et
                const isoRegex = /^\d{4}-\d{2}-\d{2}/;
                let date;
                if (isoRegex.test(str)) {
                    date = new Date(str);
                } else {
                    date = new Date(str);
                }
                if (isNaN(date.getTime())) return '-';
                const formatted = date.toLocaleDateString('tr-TR');
                cache.set(str, formatted);
                return formatted;
            } catch (e) {
                return '-';
            }
        };
    })(),

    // Safe number formatting
    formatNumber: (num, decimals = 1) => {
        if (num === null || num === undefined || num === '') return '0';
        const parsed = parseFloat(num);
        return isNaN(parsed) ? '0' : parsed.toFixed(decimals);
    },

    // Hata metni biçimlendirici
    formatError: (err) => {
        try {
            if (!err) return 'Bilinmeyen hata';
            if (typeof err === 'string') return err;
            if (err.message && typeof err.message === 'string') return err.message;
            if (err._server_messages) {
                try {
                    const msgs = JSON.parse(err._server_messages);
                    if (Array.isArray(msgs)) return msgs.join(' \n');
                } catch {}
            }
            if (err.exc) return typeof err.exc === 'string' ? err.exc : JSON.stringify(err.exc);
            if (err.responseJSON && err.responseJSON.message) return err.responseJSON.message;
            return JSON.stringify(err);
        } catch (e) {
            return String(err);
        }
    },

    // Row class utility for modern coloring
    getRowClass: (pvcCount, camCount, isCompleted = false) => {
        if (isCompleted) return 'completed-row';
        if (pvcCount > 0 && camCount > 0) return 'mixed-row';
        if (pvcCount > 0) return 'pvc-row';
        if (camCount > 0) return 'cam-row';
        return 'default-row';
    },

    // Urgent delivery check - Cached
    isUrgentDelivery: (() => {
        const cache = new Map();
        return (deliveryDate) => {
            if (!deliveryDate) return false;
            if (cache.has(deliveryDate)) return cache.get(deliveryDate);
            
            try {
                const delivery = new Date(deliveryDate);
                const today = new Date();
                const isUrgent = delivery < today;
                cache.set(deliveryDate, isUrgent);
                return isUrgent;
            } catch {
                return false;
            }
        };
    })(),

    // Text truncation utility
    truncateText: (text, maxLength = 20, suffix = '...') => {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength - suffix.length) + suffix;
    },

    getDeliveryDate: (plannedEndDate, plannedStartDate) => {
        try {
            // Bitiş tarihi varsa doğrudan kullan
            if (plannedEndDate && plannedEndDate !== 'None' && plannedEndDate !== '') {
                // dd.mm.yyyy ise olduğu gibi, ISO ise formatla
                const str = String(plannedEndDate);
                const dmyRegex = /^\d{2}\.\d{2}\.\d{4}$/;
                if (dmyRegex.test(str)) return str;
                const d = new Date(str);
                if (!isNaN(d.getTime())) {
                    const dd = String(d.getDate()).padStart(2, '0');
                    const mm = String(d.getMonth() + 1).padStart(2, '0');
                    const yyyy = d.getFullYear();
                    return `${dd}.${mm}.${yyyy}`;
                }
            }

            // Başlangıç tarihinden 4 iş günü ekle (hafta sonları hariç)
            if (plannedStartDate && plannedStartDate !== 'None' && plannedStartDate !== '') {
                const startStr = String(plannedStartDate);
                const dmyRegex = /^(\d{2})\.(\d{2})\.(\d{4})$/;
                let startDate;
                if (dmyRegex.test(startStr)) {
                    const [, dd, mm, yyyy] = startStr.match(dmyRegex);
                    startDate = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
                } else {
                    startDate = new Date(startStr);
                }
                if (isNaN(startDate.getTime())) return '-';

                let workDaysAdded = 0;
                const date = new Date(startDate);
                while (workDaysAdded < 4) {
                    date.setDate(date.getDate() + 1);
                    const dow = date.getDay(); // 0=Sun,6=Sat
                    if (dow !== 0 && dow !== 6) {
                        workDaysAdded++;
                    }
                }
                const dd2 = String(date.getDate()).padStart(2, '0');
                const mm2 = String(date.getMonth() + 1).padStart(2, '0');
                const yyyy2 = date.getFullYear();
                return `${dd2}.${mm2}.${yyyy2}`;
            }

            return '-';
        } catch (error) {
            return '-';
        }
    }
};

// Global değişkenler
let allPlannedData = [];
let showCompletedItems = false;
let updateInterval = null;
let debounceTimer = null;
let plannedSort = { column: null, direction: 'asc' };

// Performans optimizasyonları
let dataCache = new Map();
let lastCacheUpdate = 0;
const CACHE_DURATION = 30000; // 30 saniye
const DATA_LOAD_TIMEOUT = 120000; // 120 saniye timeout

const modalManager = {
    activeModals: new Set(),
    modalCache: new Map(),
    CACHE_DURATION: 60000, // 1 minute
    
    closeAllModals() {
    $('.modal').modal('hide');
    setTimeout(() => {
        $('.modal').remove();
            this.activeModals.clear();
    }, 300);
    },

    closeOtherModals(currentModalId) {
    $('.modal').not(`#${currentModalId}`).modal('hide');
    setTimeout(() => {
        $('.modal').not(`#${currentModalId}`).remove();
    }, 300);
    },

    createModal(modalId, title, size = 'modal-lg', headerColor = '#dc3545') {

    
        // Close other modals first
        this.closeOtherModals(modalId);
    
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1" data-backdrop="static" data-keyboard="false">
            <div class="modal-dialog ${size}">
                    <div class="modal-content" style="background: white; border: none; border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.1);">
                        <div class="modal-header" style="background: ${headerColor}; color: white; border: none; border-radius: 12px 12px 0 0;">
                            <h5 class="modal-title" style="font-weight: 600;">
                                <i class="fa fa-spinner fa-spin mr-2"></i>${utils.escapeHtml(title)}
                        </h5>
                            <button type="button" class="close text-white" data-dismiss="modal" style="opacity: 1;">
                                <span style="font-size: 1.5rem;">&times;</span>
                        </button>
                    </div>
                        <div class="modal-body" style="max-height: 70vh; overflow-y: auto; background: white; color: #333; padding: 20px;">
                        <div id="modal-content-${modalId}" class="modal-content-inner">
                            <div class="text-center p-4">
                                <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                                <p class="mt-2 text-muted">Yükleniyor...</p>
                            </div>
                        </div>
                    </div>
                        <div class="modal-footer" style="background: #f8f9fa; border: none; border-radius: 0 0 12px 12px;">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">
                                <i class="fa fa-times mr-1"></i>Kapat
                            </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    try {
        $('body').append(modalHtml);
        const modal = $(`#${modalId}`);
        
        if (!modal.length) {
            return null;
        }
        
            modal.on('hidden.bs.modal', () => {
                $(modal).remove();
                this.activeModals.delete(modalId);
            });
            
            modal.on('shown.bs.modal', () => {
                // Focus management for accessibility
                const firstInput = modal.find('input, button, select, textarea').first();
                if (firstInput.length) {
                    firstInput.focus();
                }
            });
            
            this.activeModals.add(modalId);
        modal.modal('show');
        

        return modal;
            
    } catch (error) {
            errorHandler.show('Modal oluşturulurken hata oluştu: ' + error.message);
        return null;
    }
    },
    
    updateModalTitle(modalId, newTitle, icon = 'fa-info-circle') {
        const modal = $(`#${modalId}`);
        if (modal.length) {
            modal.find('.modal-title').html(`<i class="fa ${icon} mr-2"></i>${utils.escapeHtml(newTitle)}`);
        }
    },
    
    updateModalContent(modalId, content) {
        const contentDiv = $(`#modal-content-${modalId}`);
        if (contentDiv.length) {
            contentDiv.html(content);
        }
    },
    
    showModalLoading(modalId, message = 'Yükleniyor...') {
        const contentDiv = $(`#modal-content-${modalId}`);
        if (contentDiv.length) {
            contentDiv.html(`
                <div class="text-center p-4">
                    <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                    <p class="mt-2 text-muted">${utils.escapeHtml(message)}</p>
                </div>
            `);
        }
    }
};

// Global references for backward compatibility
let activeModals = modalManager.activeModals;
let modalCache = modalManager.modalCache;
const MODAL_CACHE_DURATION = 60000; // 1 dakika

function closeAllModals() {
    modalManager.closeAllModals();
}

function closeOtherModals(currentModalId) {
    modalManager.closeOtherModals(currentModalId);
}

function createModal(modalId, title, size = 'modal-lg') {
    return modalManager.createModal(modalId, title, size);
}

function createPageStructure(container) {
    container.html(`
        <div class="container-fluid">

            

            
            <!-- Ana Tablo - Sadece Planlanan Siparişler -->
            <div id="planned-table-section" class="card">
                <div class="card-header" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            <div class="mr-3">
                                <i class="fa fa-check-circle" style="font-size: 1.5rem;"></i>
                            </div>
                            <div>
                                <h5 class="mb-0" style="font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">PLANLANAN ÜRETİMLER</h5>
                            </div>
                        </div>
                        <div class="d-flex align-items-center">
                            <div class="clickable-toggle mr-3" id="showCompletedToggle" data-show-completed="true" style="color: white; font-size: 0.9rem; cursor: pointer; user-select: none;">
                                <i class="fa fa-check-circle mr-1"></i><span id="toggleText">Tamamlananları Göster</span> (<span id="completedCount">0</span>)
                            </div>
                            <div class="badge badge-light" id="planlanan-count" style="font-size: 1.1rem; padding: 8px 12px; border-radius: 20px;">0</div>
                        </div>
                    </div>
                </div>
                
                <!-- Modern Filtreler -->
                <div class="card-body p-2" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-bottom: 1px solid #dee2e6;">
                    <div class="filter-single-row">
                        <div class="filter-inputs">
                            <div class="filter-input-item">
                                <input type="text" id="optiNoFilter" class="form-control form-control-sm" placeholder="Opti No...">
                            </div>
                            <div class="filter-input-item">
                                <input type="text" id="siparisNoFilter" class="form-control form-control-sm" placeholder="Sipariş No...">
                            </div>
                            <div class="filter-input-item">
                                <input type="text" id="bayiFilter" class="form-control form-control-sm" placeholder="Bayi...">
                            </div>
                            <div class="filter-input-item">
                                <input type="text" id="musteriFilter" class="form-control form-control-sm" placeholder="Müşteri...">
                            </div>
                            <div class="filter-input-item">
                                <input type="text" id="seriFilter" class="form-control form-control-sm" placeholder="Seri...">
                            </div>
                            <div class="filter-input-item">
                                <input type="text" id="renkFilter" class="form-control form-control-sm" placeholder="Renk...">
                            </div>
                            <div class="filter-input-item">
                                <select id="durumFilter" class="form-control form-control-sm">
                                    <option value="tumu">Tümü</option>
                                    <option value="pvc">PVC</option>
                                    <option value="cam">Cam</option>
                                    <option value="karisik">Karışık</option>
                                </select>
                            </div>

                            <div class="filter-input-item">
                                <button type="button" id="clearFiltersBtn" class="btn btn-sm btn-danger">
                                    <i class="fa fa-times"></i> Temizle
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card-body p-0">
                    <div class="table-container">
                        <table class="table table-hover mb-0">
                            <thead>
                                <tr>
                                    <th style="width: 5%;">HAFTA</th>
                                    <th style="width: 7%;">OPTİ NO</th>
                                    <th style="width: 12%;">SİPARİŞ NO</th>
                                    <th style="width: 10%;">BAYİ</th>
                                    <th style="width: 14%;">MÜŞTERİ</th>
                                    <th style="width: 8%;">SİPARİŞ TARİHİ</th>
                                    <th style="width: 8%;">TESLİM TARİHİ</th>
                                    <th style="width: 4%;">PVC</th>
                                    <th style="width: 4%;">CAM</th>
                                    <th style="width: 8%;">MTÜL/M²</th>
                                    <th style="width: 8%; cursor:pointer;" class="sortable-header" data-sort="baslangic">BAŞLANGIÇ</th>
                                    <th style="width: 12%;">SERİ</th>
                                    <th style="width: 12%;">RENK</th>
                                </tr>
                            </thead>
                            <tbody id="plannedTableBody">
                                <tr>
                                    <td colspan="13" class="text-center text-muted">
                                        <i class="fa fa-info-circle mr-2"></i>Henüz planlama bulunmuyor
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `);
} 

function bindEvents() {
    // Filtre input'ları
    ['optiNo', 'siparisNo', 'bayi', 'musteri', 'seri', 'renk'].forEach(filter => {
        const element = document.getElementById(filter + 'Filter');
        if (element) {
            element.addEventListener('input', () => {
                debouncedApplyFilters();
            });
        }
    });
    
    // Durum filtresi
    const durumFilter = document.getElementById('durumFilter');
    if (durumFilter) {
        durumFilter.addEventListener('change', () => {
            debouncedApplyFilters();
        });
    }
    
    // Tamamlananları göster/gizle toggle
    const showCompletedToggle = document.getElementById('showCompletedToggle');
    if (showCompletedToggle) {
        showCompletedToggle.addEventListener('click', () => {
            toggleCompletedVisibility();
        });
    }
    
    // Temizle butonu
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            clearFilters();
        });
    }
    
    // Tarih sütunu sıralama (sipariş, teslim, başlangıç)
    const table = document.querySelector('#planned-table-section table');
    if (table) {
        table.addEventListener('click', (e) => {
            const header = e.target.closest('.sortable-header');
            if (!header) return;
            const key = header.dataset.sort;
            if (!key) return;

            // current direction toggle
            const dir = header.dataset.dir === 'asc' ? 'desc' : 'asc';
            header.dataset.dir = dir;

            // map to data field
            const map = {
                siparis: 'siparis_tarihi',
                teslim: 'bitis_tarihi',
                baslangic: 'planlanan_baslangic_tarihi'
            };
            const field = map[key];

            if (!allPlannedData || !field) return;

            // yeniden sırala opti grupları oluşturulmadan önce
            allPlannedData.sort((a, b) => {
                const ad = a[field] ? new Date(a[field]) : new Date(0);
                const bd = b[field] ? new Date(b[field]) : new Date(0);
                return dir === 'asc' ? ad - bd : bd - ad;
            });

            renderPlannedTable();
        });
    }
}

const apiService = {
    async call(method, args = {}, retries = 3) {
        const attempt = async (attemptNumber) => {
            try {
                return new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(new Error('Request timeout'));
                    }, DATA_LOAD_TIMEOUT);

                    frappe.call({
                        method: method,
                        args: args,
                        timeout: Math.ceil(DATA_LOAD_TIMEOUT / 1000),
                        callback: (response) => {
                            clearTimeout(timeout);
                            if (response.exc) {
                                reject(new Error(response.exc));
                            } else {
                                resolve(response.message || response);
                            }
                        },
                        error: (error) => {
                            clearTimeout(timeout);
                            reject(new Error(error));
                        }
                    });
                });
            } catch (error) {
                if (attemptNumber < retries) {
                    await new Promise(resolve => setTimeout(resolve, 1000 * attemptNumber));
                    return attempt(attemptNumber + 1);
                }
                throw error;
            }
        };
        
        return attempt(1);
    },

    async getProductionData(filters = {}) {
        try {
            const data = await this.call(
                'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_production_planning_data',
                { filters: JSON.stringify(filters) }
            );
            
            if (!data) throw new Error('Boş veri döndü');
            
            return {
                planned: Array.isArray(data) ? data : (data.planned || [])
            };
        } catch (error) {
            throw error;
        }
    }
};

function loadProductionData() {
    const now = Date.now();
    
    // Cache kontrolü
    const cacheKey = JSON.stringify(getFilters());
    const cachedData = dataCache.get(cacheKey);
    if (cachedData && (now - cachedData.timestamp) < CACHE_DURATION) {
        allPlannedData = cachedData.data;
        renderPlannedTable();
        updateCompletedToggle();
        return;
    }
    
    showLoading();
    
    const filters = getFilters();
    
    (async () => {
        try {
            const result = await apiService.getProductionData(filters);
            
            allPlannedData = result.planned || [];
            
            // Cache'e kaydet
            dataCache.set(cacheKey, {
                data: allPlannedData,
                timestamp: now
            });
            
            renderPlannedTable();
            updateCompletedToggle();
            
        } catch (error) {
            const friendly = utils.formatError(error);
            showError('Veri yüklenirken hata oluştu: ' + friendly);
        } finally {
            hideLoading();
        }
    })();
}

function getFilters() {
    const showCompletedToggle = document.getElementById('showCompletedToggle');
    return {
        opti_no: document.getElementById('optiNoFilter')?.value || '',
        siparis_no: document.getElementById('siparisNoFilter')?.value || '',
        bayi: document.getElementById('bayiFilter')?.value || '',
        musteri: document.getElementById('musteriFilter')?.value || '',
        seri: document.getElementById('seriFilter')?.value || '',
        renk: document.getElementById('renkFilter')?.value || '',
        tip: document.getElementById('durumFilter')?.value || 'tumu',
        showCompleted: showCompletedToggle ? showCompletedToggle.dataset.showCompleted === 'true' : true
    };
}

function toggleCompletedVisibility() {
    const toggle = document.getElementById('showCompletedToggle');
    const toggleText = document.getElementById('toggleText');
    const icon = toggle.querySelector('i');
    
    if (!toggle) return;
    
    const currentState = toggle.dataset.showCompleted === 'true';
    const newState = !currentState;
    
    // Dataset'i güncelle
    toggle.dataset.showCompleted = newState.toString();
    
    // Metni güncelle
    if (newState) {
        toggleText.textContent = 'Tamamlananları Gizle';
        icon.className = 'fa fa-eye-slash mr-1';
    } else {
        toggleText.textContent = 'Tamamlananları Göster';
        icon.className = 'fa fa-check-circle mr-1';
    }
    
    // Filtreleri uygula
    debouncedApplyFilters();
}

function renderPlannedTable() {
    const tbody = document.getElementById('plannedTableBody');
    if (!tbody) {
        return;
    }
    
    if (!allPlannedData || allPlannedData.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="13" class="text-center text-muted">
                <i class="fa fa-info-circle mr-2"></i>Henüz planlama bulunmuyor
            </td></tr>
        `;
        // Toplam sayıyı 0 yap
        const countBadgeEmpty = document.getElementById('planlanan-count');
        if (countBadgeEmpty) countBadgeEmpty.textContent = '0';
        return;
    }
    
    // Filtreleri al
    const filters = getFilters();
    
    // Tamamlananları göster/gizle filtresi
    let filteredData = allPlannedData;
    if (!filters.showCompleted) {
        filteredData = allPlannedData.filter(item => item.plan_status !== 'Completed');
    }
    
    // Opti numarasına göre gruplandır - Enhanced version
    const optiGroups = {};
    filteredData.forEach(order => {
        const optiNo = order.opti_no;
        if (!optiGroups[optiNo]) {
            optiGroups[optiNo] = {
                opti_no: optiNo,
                hafta: order.hafta,
                sales_orders: [],
                bayi: order.bayi,
                musteri: order.musteri,
                siparis_tarihi: order.siparis_tarihi,
                bitis_tarihi: order.bitis_tarihi,
                total_pvc: 0,
                total_cam: 0,
                total_mtul: 0,
                planlanan_baslangic_tarihi: order.planlanan_baslangic_tarihi,
                planned_end_date: order.planned_end_date,
                seri: order.seri,
                renk: order.renk,
                plan_status: order.plan_status,
                // Multiple values support
                bayi_list: new Set(),
                musteri_list: new Set(),
                seri_list: new Set(),
                renk_list: new Set()
            };
        }
        // Sipariş numarasını sadece bir kez ekle
        if (!optiGroups[optiNo].sales_orders.includes(order.sales_order)) {
            optiGroups[optiNo].sales_orders.push(order.sales_order);
        }
        optiGroups[optiNo].total_pvc += order.pvc_count || 0;
        optiGroups[optiNo].total_cam += order.cam_count || 0;
        optiGroups[optiNo].total_mtul += order.toplam_mtul_m2 || 0;
        
        // Collect multiple values
        if (order.bayi) optiGroups[optiNo].bayi_list.add(order.bayi);
        if (order.musteri) optiGroups[optiNo].musteri_list.add(order.musteri);
        if (order.seri) optiGroups[optiNo].seri_list.add(order.seri);
        if (order.renk) optiGroups[optiNo].renk_list.add(order.renk);
    });
    
    // Convert Sets to Arrays
    Object.values(optiGroups).forEach(group => {
        group.bayi_list = Array.from(group.bayi_list);
        group.musteri_list = Array.from(group.musteri_list);
        group.seri_list = Array.from(group.seri_list);
        group.renk_list = Array.from(group.renk_list);
    });
    
    // Grupları sırala
    let sortedOptiGroups = Object.values(optiGroups);
    if (plannedSort.column) {
        const dir = plannedSort.direction === 'asc' ? 1 : -1;
        sortedOptiGroups.sort((a, b) => {
            const av = a[plannedSort.column] ? new Date(a[plannedSort.column]) : new Date(0);
            const bv = b[plannedSort.column] ? new Date(b[plannedSort.column]) : new Date(0);
            return av > bv ? dir : av < bv ? -dir : 0;
        });
    } else {
        sortedOptiGroups.sort((a, b) => {
        const aCompleted = a.plan_status === 'Completed';
        const bCompleted = b.plan_status === 'Completed';
        if (aCompleted && !bCompleted) return -1;
        if (!aCompleted && bCompleted) return 1;
        const aDate = new Date(a.planlanan_baslangic_tarihi || '1900-01-01');
        const bDate = new Date(b.planlanan_baslangic_tarihi || '1900-01-01');
        return aDate - bDate;
    });
    }
    
    // Performans için DocumentFragment kullan
    const fragment = document.createDocumentFragment();
    
    sortedOptiGroups.forEach((optiGroup, index) => {
        const optiRow = createOptiRowElement(optiGroup);
        fragment.appendChild(optiRow);
    });
    
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
    
    // Toplam sayıyı güncelle (opti grubu sayısı)
    const countBadge = document.getElementById('planlanan-count');
    if (countBadge) countBadge.textContent = String(sortedOptiGroups.length);
    
    bindTableEvents();
}

function createOptiRowElement(optiGroup) {
    const row = document.createElement('tr');
    const pvcCount = optiGroup.total_pvc || 0;
    const camCount = optiGroup.total_cam || 0;
    const isCompleted = optiGroup.plan_status === 'Completed';
    const rowClass = utils.getRowClass(pvcCount, camCount, isCompleted);
    const isUrgent = utils.isUrgentDelivery(optiGroup.bitis_tarihi);
    const urgentClass = isUrgent ? 'urgent-delivery' : '';
    
    row.className = `${rowClass} ${urgentClass} opti-row cursor-pointer`;
    row.dataset.opti = optiGroup.opti_no;
    
    // Multiple values display
    const bayiText = optiGroup.bayi_list.join(', ') || '-';
    const musteriText = optiGroup.musteri_list.join(', ') || '-';
    const seriText = optiGroup.seri_list.join(', ') || '-';
    const renkText = optiGroup.renk_list.join(', ') || '-';
    
    // Truncate for display
    const truncatedBayi = utils.truncateText(bayiText, 15);
    const truncatedMusteri = utils.truncateText(musteriText, 25);
    const truncatedSeri = utils.truncateText(seriText, 15);
    const truncatedRenk = utils.truncateText(renkText, 15);
    
    // Sipariş numaralarını birleştir
    const siparisText = optiGroup.sales_orders.join(', ');
    const truncatedSiparis = utils.truncateText(siparisText, 20);
    
    // Teslim tarihi için enhanced logic
    const plannedEndDate = optiGroup.planned_end_date && optiGroup.planned_end_date !== 'None' ? optiGroup.planned_end_date : null;
    const plannedStartDate = optiGroup.planlanan_baslangic_tarihi && optiGroup.planlanan_baslangic_tarihi !== 'None' ? optiGroup.planlanan_baslangic_tarihi : null;
    
    const deliveryDate = utils.getDeliveryDate(plannedEndDate, plannedStartDate);
    
    // Güvenli tarih kontrolü
    const safeDeliveryDate = deliveryDate && deliveryDate !== '-' ? deliveryDate : '-';
    
    row.innerHTML = `
        <td class="text-center">
            <span class="badge badge-info">${utils.escapeHtml(optiGroup.hafta || '-')}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-primary">${utils.escapeHtml(optiGroup.opti_no)}</span>
        </td>
        <td title="${utils.escapeHtml(siparisText)}">
            <span class="font-weight-bold text-primary">${utils.escapeHtml(truncatedSiparis)}</span>
        </td>
        <td title="${utils.escapeHtml(bayiText)}">${utils.escapeHtml(truncatedBayi)}</td>
        <td title="${utils.escapeHtml(musteriText)}">${utils.escapeHtml(truncatedMusteri)}</td>
        <td class="text-center">
            <span class="badge badge-warning">${utils.formatDate(optiGroup.siparis_tarihi)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-danger">${utils.formatDate(safeDeliveryDate)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-danger">${pvcCount}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-primary">${camCount}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-success">${utils.formatNumber(optiGroup.total_mtul)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-warning">${utils.formatDate(optiGroup.planlanan_baslangic_tarihi)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-info">${utils.escapeHtml(truncatedSeri)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-warning">${utils.escapeHtml(truncatedRenk)}</span>
        </td>
    `;
    
    return row;
}













function updateCompletedToggle() {
    const completedCountElement = document.getElementById('completedCount');
    if (completedCountElement && allPlannedData) {
        // Opti numarasına göre gruplandır ve tamamlanan üretim planı sayısını hesapla
        const optiGroups = {};
        allPlannedData.forEach(order => {
            const optiNo = order.opti_no;
            if (!optiGroups[optiNo]) {
                optiGroups[optiNo] = {
                    opti_no: optiNo,
                    plan_status: order.plan_status
                };
            }
        });
        
        const completedCount = Object.values(optiGroups).filter(opti => opti.plan_status === 'Completed').length;
        completedCountElement.textContent = completedCount;
    }
}

const debouncedApplyFilters = utils.debounce(() => {
        loadProductionData();
    }, 500);

function startAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    
    updateInterval = setInterval(() => {
        // Only update if page is visible and no modals are open
        if (!document.hidden && 
            !document.querySelector('.modal.show') && 
            !document.querySelector('.swal2-container')) {
        
            // Add small delay to prevent concurrent updates
            setTimeout(() => {
                if (!document.hidden) {
            loadProductionData();
                }
            }, Math.random() * 1000); // Random delay 0-1 second
        }
    }, 30000); // 30 saniyede bir güncelle
    
    // Pause updates when page becomes hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        } else {
            // Restart auto-update when page becomes visible
            startAutoUpdate();
            // Immediate update when page becomes visible
            setTimeout(() => loadProductionData(), 1000);
        }
    });
}

function clearFilters() {
    // Tüm input'ları temizle
    ['optiNo', 'siparisNo', 'bayi', 'musteri', 'seri', 'renk'].forEach(filter => {
        const element = document.getElementById(filter + 'Filter');
        if (element) {
            element.value = '';
        }
    });
    
    // Durum filtresini sıfırla
    const durumFilter = document.getElementById('durumFilter');
    if (durumFilter) {
        durumFilter.value = 'tumu';
    }
    
    // Tamamlananları göster toggle'ını sıfırla
    const showCompletedToggle = document.getElementById('showCompletedToggle');
    const toggleText = document.getElementById('toggleText');
    const icon = showCompletedToggle?.querySelector('i');
    
    if (showCompletedToggle && toggleText && icon) {
        showCompletedToggle.dataset.showCompleted = 'true';
        toggleText.textContent = 'Tamamlananları Gizle';
        icon.className = 'fa fa-eye-slash mr-1';
    }
    
    // Verileri yeniden yükle
    loadProductionData();
}

function bindTableEvents() {
    const tbody = document.getElementById('plannedTableBody');
    if (!tbody) return;
    
    // Remove existing event listeners to prevent duplicates
    tbody.removeEventListener('click', handleTableClick);
    
    // Use event delegation for better performance
    tbody.addEventListener('click', handleTableClick);
}

// Table click handler
function handleTableClick(e) {
    const row = e.target.closest('tr[data-opti]');
    if (row && !e.target.closest('button') && !e.target.closest('a')) {
        e.preventDefault();
        e.stopPropagation();
                showOptiDetails(row.dataset.opti);
            }
}

function showLoading() {
    // Loading overlay'i gizli yap - kullanıcı fark etmesin
}

function hideLoading() {
    // Loading overlay'i gizli yap - kullanıcı fark etmesin
}

const errorHandler = {
    show: (message, title = 'Hata', type = 'error') => {
        try {
            if (frappe && frappe.show_alert) {
    frappe.show_alert({
        message: message,
                    indicator: type === 'error' ? 'red' : 'yellow'
    }, 5);
            }
            
            // Show detailed modal for critical errors
            if (type === 'error' && (message.includes('API') || message.includes('network') || message.includes('timeout'))) {
                errorHandler.showDetailedModal(message, title);
            }
        } catch (error) {
            // Error showing message
        }
    },
    
    showDetailedModal: (message, title) => {
        const modal = $(`
            <div class="modal fade" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fa fa-exclamation-triangle mr-2"></i>${utils.escapeHtml(title)}
                            </h5>
                            <button type="button" class="close text-white" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger">
                                <i class="fa fa-exclamation-circle mr-2"></i>
                                <strong>Hata Detayı:</strong><br>
                                ${utils.escapeHtml(message)}
                            </div>
                            <div class="mt-3">
                                <button class="btn btn-primary" onclick="loadProductionData()">
                                    <i class="fa fa-refresh mr-2"></i>Tekrar Dene
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        modal.modal('show');
        
        // Auto close after 10 seconds
        setTimeout(() => {
            modal.modal('hide');
        }, 10000);
    }
};

function showError(message, title = 'Hata') {
    errorHandler.show(message, title, 'error');
}



// Modal fonksiyonları
function showOptiDetails(optiNo) {
    if (!optiNo) {
        errorHandler.show('Geçersiz Opti numarası');
        return;
    }
    
    const modalId = 'opti-details-' + Date.now();
    const cacheKey = `opti-details-${optiNo}`;
    
    // Check cache first
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        const modal = modalManager.createModal(
            modalId, 
            `Opti ${optiNo} - Sipariş Detayları`,
            'modal-xl',
            '#dc3545'
        );
        if (modal) {
            setTimeout(() => {
                updateOptiDetailsModal(cachedData.data, modalId);
            }, 100);
        }
        return;
    }
                    
    const modal = modalManager.createModal(
        modalId, 
        `Opti ${optiNo} - Sipariş Detayları`,
        'modal-xl',
        '#dc3545'
    );
    
    if (!modal) return;
    
    (async () => {
        try {
            const data = await apiService.call(
                'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_opti_details_for_takip',
                { opti_no: optiNo }
            );
            
            if (!data) {
                throw new Error('Opti detayları alınamadı');
            }
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Cache the data
            modalCache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            updateOptiDetailsModal(data, modalId);
            
        } catch (error) {
            modalManager.updateModalContent(modalId, `
                <div class="alert alert-danger">
                    <i class="fa fa-exclamation-triangle mr-2"></i>
                    <strong>Hata:</strong> ${utils.escapeHtml(error.message)}
                </div>
                <div class="text-center">
                    <button class="btn btn-primary" onclick="showOptiDetails('${optiNo}')">
                        <i class="fa fa-refresh mr-2"></i>Tekrar Dene
                    </button>
                </div>
            `);
        }
    })();
}

function showOrderDetails(salesOrder) {
    const modalId = 'order-details-' + Date.now();
    const cacheKey = `order-details-${salesOrder}`;
    
    // Cache kontrolü
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        const modal = createModal(modalId, `Sipariş: ${salesOrder}`, 'modal-xl');
        setTimeout(() => {
            updateOrderDetailsModal(cachedData.data, modalId);
        }, 100);
        return;
    }
    
    const modal = createModal(modalId, `Sipariş: ${salesOrder}`, 'modal-xl');
    
    // API çağrısı
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_sales_order_details_for_takip',
        args: { sales_order: salesOrder },
        timeout: 15,
        callback: function(r) {
            if (r.exc) {
                showError('Sipariş detayları yüklenirken hata: ' + r.exc);
                modal.modal('hide');
                return;
            }
            
            const data = r.message;
            if (data.error) {
                showError(data.error);
                modal.modal('hide');
                return;
            }
            
            // Cache'e kaydet
            modalCache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            updateOrderDetailsModal(data, modalId);
        }
    });
}

function showWorkOrders(salesOrder, optiNo = null, typeHint = '') {
    if (!salesOrder) {
        errorHandler.show('Geçersiz sipariş numarası');
        return;
    }
    
    // Eğer panel stilindeki modal fonksiyonu mevcutsa onu kullan
    if (window.showWorkOrdersPaneli && typeof window.showWorkOrdersPaneli === 'function') {
        try {

            // Panel tarafındaki modal backend'e production_plan (opti) bilgisini iletebiliyor
            window.showWorkOrdersPaneli(salesOrder, optiNo || null);
            return;
        } catch (e) {
            // Panel fonksiyonu çağrılamadı, yerel modal kullanılacak
        }
    }
    
    
    
    const modalId = 'work-orders-' + Date.now();
    const cacheKey = `work-orders-${salesOrder}-${optiNo || 'all'}-${typeHint || 'any'}`;
    
    // Check cache first
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        
        const modal = modalManager.createModal(
            modalId, 
            `İş Emirleri - ${salesOrder}`,
            'modal-xl',
            '#28a745'
        );
        if (modal) {
            setTimeout(() => {
                updateWorkOrdersModal(cachedData.data, modalId, salesOrder);
            }, 100);
        }
        return;
    }
    
    const modal = modalManager.createModal(
        modalId, 
        `İş Emirleri - ${salesOrder}`,
        'modal-xl',
        '#ffc107'
    );
    
    if (!modal) {
        errorHandler.show('Modal oluşturulamadı');
        return;
    }
    
    (async () => {
        try {
            modalManager.showModalLoading(modalId, 'İş emirleri yükleniyor...');
            
            const data = await apiService.call(
                'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_work_orders_for_takip',
                { sales_order: salesOrder, production_plan: optiNo || null }
            );
            
            if (!data) {
                throw new Error('İş emirleri verisi alınamadı');
            }
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Opti'ye göre filtrele (varsa) - sayı tabanlı esnek karşılaştırma
            let filtered = data;
            const list = Array.isArray(data) ? data : (data.work_orders || []);
            if (optiNo) {
                const target = normalizeId(optiNo);
                let woFiltered = list.filter(wo => {
                    const candidates = [wo.opti_no, wo.opti, wo.production_plan, wo.production_plan_name, wo.production_plan_id];
                    return candidates.some(c => normalizeId(c) === target);
                });
                // Tür ipucuna göre (pvc/cam) ek filtre
                if (typeHint === 'cam') {
                    woFiltered = woFiltered.filter(wo => (wo.is_cam || wo.type === 'Cam' || /cam/i.test(wo.item_group || '') || /cam/i.test(wo.operation || '')));
                } else if (typeHint === 'pvc') {
                    woFiltered = woFiltered.filter(wo => (wo.is_pvc || wo.type === 'PVC' || /pvc/i.test(wo.item_group || '') || /profil|pvc/i.test(wo.operation || '')));
                }
                // Plan kapsamındaki kalemlerle sınırla (varsa)
                try {
                    const visibleOrderItems = (window.currentOptiOrderItems && Array.isArray(window.currentOptiOrderItems)) ? window.currentOptiOrderItems.map(String) : null;
                    if (visibleOrderItems && visibleOrderItems.length > 0) {
                        woFiltered = woFiltered.filter(wo => {
                            const soItem = String(wo.sales_order_item || wo.so_detail || wo.production_item || '');
                            return visibleOrderItems.includes(soItem);
                        });
                    }
                } catch (e) { /* order item constraint skipped */ }
                // Eşleşme bulunamazsa tüm işi göstermek için geri dönüş yap
                if (woFiltered.length === 0) {
                    filtered = data;
                } else {
                    filtered = Array.isArray(data) ? woFiltered : { ...data, work_orders: woFiltered };
                }
            }
            
            // Cache the data
            modalCache.set(cacheKey, {
                data: filtered,
                timestamp: Date.now()
            });
            
            updateWorkOrdersModal(filtered, modalId, salesOrder);
            
        } catch (error) {
            modalManager.updateModalContent(modalId, `
                <div class="alert alert-danger">
                    <i class="fa fa-exclamation-triangle mr-2"></i>
                    <strong>Hata:</strong> ${utils.escapeHtml(error.message)}
                </div>
                <div class="text-center">
                    <button class="btn btn-primary" onclick="showWorkOrders('${salesOrder}','${optiNo || ''}')">
                        <i class="fa fa-refresh mr-2"></i>Tekrar Dene
                    </button>
                </div>
            `);
        }
    })();
}

function updateOptiDetailsModal(data, modalId) {
    if (!data || !data.orders) {
        modalManager.updateModalContent(modalId, `
            <div class="alert alert-warning">
                <i class="fa fa-exclamation-triangle mr-2"></i>
                Opti detayları bulunamadı
            </div>
        `);
        return;
    }
    
    // Başlık
    modalManager.updateModalTitle(modalId, `Opti ${data.opti_no} - Sipariş Detayları`, 'fa-cogs');
    
    // Sipariş bazında grupla
    const groupedOrders = groupOrdersBySalesOrder(data.orders);

    // Özetler
    const totals = groupedOrders.reduce((acc, o) => {
        acc.total_pvc += parseInt(o.pvc_count || 0);
        acc.total_cam += parseInt(o.cam_count || 0);
        acc.total_mtul += parseFloat(o.total_mtul || 0);
        return acc;
    }, { total_pvc: 0, total_cam: 0, total_mtul: 0 });

    const tableBodyId = `modal-order-rows-${modalId}`;
    const sipFilterId = `modal-siparis-filter-${modalId}`;
    const bayiFilterId = `modal-bayi-filter-${modalId}`;
    const musFilterId = `modal-musteri-filter-${modalId}`;
    const seriFilterId = `modal-seri-filter-${modalId}`;
    const renkFilterId = `modal-renk-filter-${modalId}`;
    const clearBtnId = `modal-clear-filters-${modalId}`;
    
    const html = `
        <div class="alert alert-info d-flex align-items-center mb-4">
            <i class="fa fa-info-circle mr-3" style="font-size: 1.5rem;"></i>
            <div>
                <h6 class="mb-0"><strong>Opti ${utils.escapeHtml(data.opti_no)}</strong></h6>
                <small>Toplam ${groupedOrders.length} sipariş planlandı</small>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card border-0 shadow-sm">
                    <div class="card-body text-center" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; border-radius: 12px;">
                        <i class="fa fa-cube mb-2" style="font-size: 2rem; opacity: 0.8;"></i>
                        <h3 class="mb-1">${totals.total_pvc}</h3>
                        <small style="font-weight: 500;">Toplam PVC Adedi</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm">
                    <div class="card-body text-center" style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); color: white; border-radius: 12px;">
                        <i class="fa fa-square mb-2" style="font-size: 2rem; opacity: 0.8;"></i>
                        <h3 class="mb-1">${totals.total_cam}</h3>
                        <small style="font-weight: 500;">Toplam Cam Adedi</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card border-0 shadow-sm">
                    <div class="card-body text-center" style="background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); color: white; border-radius: 12px;">
                        <i class="fa fa-calculator mb-2" style="font-size: 2rem; opacity: 0.8;"></i>
                        <h3 class="mb-1">${utils.formatNumber(totals.total_mtul || 0, 2)}</h3>
                        <small style="font-weight: 500;">Toplam MTÜL/m²</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card border-0 shadow-sm mb-3">
            <div class="card-body py-2">
                <div class="d-flex flex-wrap align-items-center" style="gap: 6px;">
                    <input id="${sipFilterId}" class="form-control form-control-sm" style="max-width: 160px;" placeholder="Sipariş No..." />
                    <input id="${bayiFilterId}" class="form-control form-control-sm" style="max-width: 160px;" placeholder="Bayi..." />
                    <input id="${musFilterId}" class="form-control form-control-sm" style="max-width: 180px;" placeholder="Müşteri..." />
                    <input id="${seriFilterId}" class="form-control form-control-sm" style="max-width: 160px;" placeholder="Seri..." />
                    <input id="${renkFilterId}" class="form-control form-control-sm" style="max-width: 160px;" placeholder="Renk..." />
                    <button id="${clearBtnId}" class="btn btn-sm btn-danger"><i class="fa fa-times mr-1"></i>Temizle</button>
                </div>
            </div>
        </div>

        <div class="card border-0 shadow-sm">
            <div class="card-header" style="background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%); color: white; border-radius: 12px 12px 0 0;">
                <h6 class="mb-0"><i class="fa fa-list mr-2"></i>Sipariş Detayları</h6>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white;">
                            <tr>
                                <th style="border: none; padding: 8px 6px; width: 12%;">Sipariş No</th>
                                <th style="border: none; padding: 8px 6px; width: 12%;">Bayi</th>
                                <th style="border: none; padding: 8px 6px; width: 12%;">Müşteri</th>
                                <th style="border: none; padding: 8px 6px; width: 10%;">Seri</th>
                                <th style="border: none; padding: 8px 6px; width: 10%;">Renk</th>
                                <th style="border: none; padding: 8px 6px; width: 8%;">Adet</th>
                                <th style="border: none; padding: 8px 6px; width: 10%;">MTÜL/m²</th>
                                <th style="border: none; padding: 8px 6px; width: 18%;">Durum & Açıklama</th>
                                <th style="border: none; padding: 8px 6px; width: 10%;">İşlemler</th>
                            </tr>
                        </thead>
                        <tbody id="${tableBodyId}" style="background: white;"></tbody>
                    </table>
                </div>
            </div>
        </div>`;
    
    modalManager.updateModalContent(modalId, html);

    // İlk render
    const renderRows = (rows) => {
        const tbody = document.getElementById(tableBodyId);
        if (!tbody) return;
        if (!rows || rows.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">Kayıt bulunamadı</td></tr>`;
            return;
        }
        tbody.innerHTML = generateGroupedOrderRows(rows, data.opti_no);
    };

    renderRows(groupedOrders);

    // Filtre bağla
    const getValue = (id) => (document.getElementById(id)?.value || '').toLowerCase();
    const applyFilters = () => {
        const fSip = getValue(sipFilterId);
        const fBayi = getValue(bayiFilterId);
        const fMus = getValue(musFilterId);
        const fSeri = getValue(seriFilterId);
        const fRenk = getValue(renkFilterId);
        const filtered = groupedOrders.filter(o =>
            (!fSip || String(o.sales_order).toLowerCase().includes(fSip)) &&
            (!fBayi || (o.bayi_text || '').toLowerCase().includes(fBayi)) &&
            (!fMus || (o.musteri_text || '').toLowerCase().includes(fMus)) &&
            (!fSeri || (o.seri_text || '').toLowerCase().includes(fSeri)) &&
            (!fRenk || (o.renk_text || '').toLowerCase().includes(fRenk))
        );
        renderRows(filtered);
    };

    [sipFilterId, bayiFilterId, musFilterId, seriFilterId, renkFilterId].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', utils.debounce(applyFilters, 250));
    });

    const clearBtn = document.getElementById(clearBtnId);
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            [sipFilterId, bayiFilterId, musFilterId, seriFilterId, renkFilterId].forEach(id => {
                const el = document.getElementById(id); if (el) el.value = '';
            });
            renderRows(groupedOrders);
        });
    }
}

// Helper function to calculate opti totals
function calculateOptiTotals(orders) {
    return orders.reduce((totals, order) => {
        totals.total_pvc += parseInt(order.pvc_qty || order.pvc_count || 0);
        totals.total_cam += parseInt(order.cam_qty || order.cam_count || 0);
        totals.total_mtul += parseFloat(order.total_mtul || order.toplam_mtul_m2 || 0);
        return totals;
    }, { total_pvc: 0, total_cam: 0, total_mtul: 0 });
}

// Helper function to generate order rows
function generateOptiOrderRows(orders) {
    const grouped = Array.isArray(orders) && orders.length && orders[0] && orders[0]._grouped
        ? orders
        : groupOrdersBySalesOrder(orders);
    return generateGroupedOrderRows(grouped);
}

function generateGroupedOrderRows(groupedOrders, optiNoForOrders = '') {
    return groupedOrders.map(order => {
        const orderDate = utils.formatDate(order.siparis_tarihi);
        const description = order.aciklama || order.siparis_aciklama || order.remarks || 'Açıklama yok';
        const isUrgent = order.is_urgent || order.urgent || false;
        const urgencyBadge = isUrgent ? 
            '<span class="badge badge-danger mr-1"><i class="fa fa-exclamation-triangle"></i> ACİL</span>' : 
            '<span class="badge badge-success mr-1"><i class="fa fa-check-circle"></i> NORMAL</span>';
        
        const pvcCount = parseInt(order.pvc_count || 0);
        const camCount = parseInt(order.cam_count || 0);
        const mtul = parseFloat(order.total_mtul || 0);
        const adetText = pvcCount > 0 ? `${pvcCount} PVC` : `${camCount} Cam`;

        const seriText = order.seri_text || '-';
        const renkText = order.renk_text || '-';
        const bayiText = order.bayi_text || order.bayi || '-';
        const musteriText = order.musteri_text || order.musteri || '-';
        
        // Tür ipucu: sadece cam veya sadece pvc ise belirle
        const typeHint = (camCount > 0 && pvcCount === 0) ? 'cam' : (pvcCount > 0 && camCount === 0) ? 'pvc' : '';
        
        return `
            <tr style="transition: all 0.2s ease;">
                <td style="padding: 8px 6px;">
                    <div class="d-flex flex-column">
                        <span class="badge badge-info mb-1" style="font-size: 0.7rem;">${utils.escapeHtml(order.sales_order || '-')}</span>
                        <small class="text-muted" style="font-size: 0.65rem;">${orderDate}</small>
                    </div>
                </td>
                <td style="padding: 8px 6px; font-size: 0.8rem; white-space: normal; word-break: break-word;">${utils.escapeHtml(bayiText)}</td>
                <td style="padding: 8px 6px; font-size: 0.8rem; white-space: normal; word-break: break-word;">${utils.escapeHtml(musteriText)}</td>
                <td style="padding: 8px 6px;">
                    <span class="badge badge-info" style="font-size: 0.7rem;">${utils.escapeHtml(seriText)}</span>
                </td>
                <td style="padding: 8px 6px;">
                    <span class="badge badge-warning" style="font-size: 0.7rem;">${utils.escapeHtml(renkText)}</span>
                </td>
                <td class="text-center" style="padding: 8px 6px;">
                    <span class="badge badge-danger" style="font-size: 0.7rem;">${utils.escapeHtml(adetText)}</span>
                </td>
                <td style="padding: 8px 6px;">
                    <span class="badge badge-success" style="font-size: 0.7rem;">${utils.formatNumber(mtul, 2)}</span>
                </td>
                <td style="padding: 8px 6px;">
                    <div class="mb-1">${urgencyBadge}</div>
                    <small class="text-muted" style="font-size: 0.65rem; white-space: normal; word-break: break-word;">${utils.escapeHtml(description)}</small>
                </td>
                <td style="padding: 8px 6px;">
                    <div class="btn-group-vertical" style="width: 88px;">
                        <a href="/app/sales-order/${order.sales_order}" target="_blank" 
                           class="btn btn-sm btn-success text-white" 
                           style="padding: 6px 8px; font-size: 0.8rem;">
                            <i class="fa fa-external-link mr-1"></i>Sipariş
                        </a>
                        <button class="btn btn-sm btn-warning" 
                                onclick="showWorkOrders('${order.sales_order}','${optiNoForOrders}','${typeHint}')" 
                                style="padding: 8px 8px; font-size: 0.8rem; line-height: 1.1; color: #000;">
                            <i class="fa fa-cogs mr-1"></i>İş<br>Emirleri
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function groupOrdersBySalesOrder(orders) {
    const map = {};
    (orders || []).forEach(o => {
        const key = o.sales_order || '-';
        if (!map[key]) {
            map[key] = {
                _grouped: true,
                sales_order: key,
                bayi_set: new Set(),
                musteri_set: new Set(),
                seri_set: new Set(),
                renk_set: new Set(),
                item_set: new Set(),
                pvc_count: 0,
                cam_count: 0,
                total_mtul: 0,
                siparis_tarihi: o.siparis_tarihi,
                aciklama: o.siparis_aciklama || o.remarks || ''
            };
        }
        if (o.bayi) map[key].bayi_set.add(o.bayi);
        if (o.musteri) map[key].musteri_set.add(o.musteri);
        if (o.seri) map[key].seri_set.add(o.seri);
        if (o.renk) map[key].renk_set.add(o.renk);
        if (o.so_detail) map[key].item_set.add(String(o.so_detail));
        if (o.sales_order_item) map[key].item_set.add(String(o.sales_order_item));
        if (o.production_item) map[key].item_set.add(String(o.production_item));
        map[key].pvc_count += parseInt(o.pvc_qty || o.pvc_count || 0) || 0;
        map[key].cam_count += parseInt(o.cam_qty || o.cam_count || 0) || 0;
        map[key].total_mtul += parseFloat(o.total_mtul || o.toplam_mtul_m2 || 0) || 0;
    });

    return Object.values(map).map(g => ({
        ...g,
        bayi_text: Array.from(g.bayi_set).join(', '),
        musteri_text: Array.from(g.musteri_set).join(', '),
        seri_text: Array.from(g.seri_set).join(', '),
        renk_text: Array.from(g.renk_set).join(', '),
        item_list: Array.from(g.item_set)
    }));
}

function updateOrderDetailsModal(data, modalId) {
    if (!data) {
        modalManager.updateModalContent(modalId, `
            <div class="alert alert-warning">
                <i class="fa fa-exclamation-triangle mr-2"></i>
                Sipariş detayları bulunamadı
                </div>
        `);
        return;
    }
    
    const isUrgent = data.acil || data.is_urgent || false;
    const urgencyBadge = isUrgent ? 
        '<span class="badge badge-danger"><i class="fa fa-exclamation-triangle mr-1"></i>ACİL</span>' : 
        '<span class="badge badge-success"><i class="fa fa-check-circle mr-1"></i>NORMAL</span>';
    
    const html = `
        <!-- Order Info Header -->
        <div class="alert alert-info d-flex align-items-center mb-4">
            <i class="fa fa-shopping-cart mr-3" style="font-size: 1.5rem;"></i>
            <div>
                <h6 class="mb-0"><strong>Sipariş: ${utils.escapeHtml(data.sales_order || '-')}</strong></h6>
                <small>Sipariş detay bilgileri</small>
            </div>
        </div>
        
        <div class="row">
            <!-- Order Information -->
            <div class="col-md-6">
                <div class="card border-0 shadow-sm mb-3">
                    <div class="card-header" style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white;">
                        <h6 class="mb-0">
                            <i class="fa fa-shopping-cart mr-2"></i>Sipariş Bilgileri
                        </h6>
            </div>
                    <div class="card-body">
                        <table class="table table-sm mb-0">
                            <tbody>
                                <tr>
                                    <td><strong>Sipariş No:</strong></td>
                                    <td><span class="badge badge-primary">${utils.escapeHtml(data.sales_order || '-')}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Bayi:</strong></td>
                                    <td>${utils.escapeHtml(data.bayi || '-')}</td>
                                </tr>
                                <tr>
                                    <td><strong>Müşteri:</strong></td>
                                    <td>${utils.escapeHtml(data.musteri || '-')}</td>
                                </tr>
                                <tr>
                                    <td><strong>Sipariş Tarihi:</strong></td>
                                    <td><span class="badge badge-warning">${utils.formatDate(data.siparis_tarihi)}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Teslim Tarihi:</strong></td>
                                    <td><span class="badge badge-danger">${utils.formatDate(data.bitis_tarihi)}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Öncelik:</strong></td>
                                    <td>${urgencyBadge}</td>
                                </tr>
                            </tbody>
                </table>
            </div>
        </div>
                </div>
            
            <!-- Production Information -->
            <div class="col-md-6">
                <div class="card border-0 shadow-sm mb-3">
                    <div class="card-header" style="background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); color: white;">
                            <h6 class="mb-0">
                            <i class="fa fa-cogs mr-2"></i>Üretim Bilgileri
                            </h6>
                        </div>
                    <div class="card-body">
                        <table class="table table-sm mb-0">
                            <tbody>
                                <tr>
                                    <td><strong>Opti No:</strong></td>
                                    <td><span class="badge badge-warning">${utils.escapeHtml(data.opti_no || '-')}</span></td>
                                        </tr>
                                <tr>
                                    <td><strong>Seri:</strong></td>
                                    <td><span class="badge badge-info">${utils.escapeHtml(data.seri || '-')}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Renk:</strong></td>
                                    <td><span class="badge badge-warning">${utils.escapeHtml(data.renk || '-')}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>PVC Adet:</strong></td>
                                    <td><span class="badge badge-danger">${data.pvc_count || 0}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Cam Adet:</strong></td>
                                    <td><span class="badge badge-primary">${data.cam_count || 0}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Toplam MTÜL:</strong></td>
                                    <td><span class="badge badge-success">${utils.formatNumber(data.toplam_mtul || 0, 2)}</span></td>
                                        </tr>
                                    </tbody>
                </table>
                    </div>
                            </div>
            </div>
        </div>
        
        ${data.aciklama ? `
        <!-- Description Section -->
        <div class="row">
            <div class="col-12">
                <div class="card border-0 shadow-sm">
                    <div class="card-header" style="background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%); color: white;">
                        <h6 class="mb-0">
                            <i class="fa fa-comment mr-2"></i>Açıklama
                            </h6>
                        </div>
                    <div class="card-body">
                        <div class="alert alert-info mb-0">
                            ${utils.escapeHtml(data.aciklama)}
                            </div>
                    </div>
                </div>
            </div>
        </div>
        ` : ''}
        
        <!-- Action Buttons -->
        <div class="row mt-3">
            <div class="col-12 text-center">
                <div class="btn-group" role="group">
                    <a href="/app/sales-order/${data.sales_order}" target="_blank" class="btn btn-primary">
                        <i class="fa fa-external-link mr-2"></i>Siparişi Aç
                    </a>
                    <button class="btn btn-success" onclick="showWorkOrders('${data.sales_order}')">
                        <i class="fa fa-cogs mr-2"></i>İş Emirlerini Gör
                    </button>
                        </div>
                    </div>
                </div>
            `;
            
    modalManager.updateModalContent(modalId, html);
}

// Güvenli ID üretici (özel karakter sorunlarını önler)
function makeSafeId(value) {
    return String(value || '')
        .replace(/\s+/g, '_')
        .replace(/[^a-zA-Z0-9_-]/g, '_');
}

function normalizeId(value) {
    try {
        return String(value || '').replace(/\D+/g, '');
    } catch {
        return '';
    }
}

function updateWorkOrdersModal(data, modalId, salesOrder) {
    // Başlık ikonunu ayarla
    modalManager.updateModalTitle(modalId, `İş Emirleri - ${salesOrder}`, 'fa-list');
    
    if (!data || (!Array.isArray(data) && !data.work_orders)) {
        modalManager.updateModalContent(modalId, `
            <div class="alert alert-info text-center">
                <i class="fa fa-info-circle mr-2"></i>Bu sipariş için iş emri bulunamadı
            </div>`);
        return;
    }
    
    const workOrders = Array.isArray(data) ? data : (data.work_orders || []);
    if (workOrders.length === 0) {
        modalManager.updateModalContent(modalId, `
            <div class="alert alert-warning text-center">
                <i class="fa fa-exclamation-triangle mr-2"></i>Bu sipariş için henüz iş emri oluşturulmamış
            </div>`);
        return;
    }
    
    const html = `
        <div class="wo-accordion">
            ${workOrders.map((wo, idx) => {
                const statusBadge = getWorkOrderStatusBadge(wo.status);
                const open = 'none';
                const pozLabel = getWorkOrderPozLabel(wo);
                const safeId = makeSafeId(wo.name);
                return `
                    <div class="card mb-3" style="border: 1px solid #e9ecef; border-radius: 8px;">
                        <div class="d-flex justify-content-between align-items-center" 
                             style="background:#f8f9fa; border-radius:8px 8px 0 0; padding:10px 12px; cursor:pointer;"
                             onclick="toggleWorkOrderSection('${safeId}', '${wo.name}')">
                            <div class="d-flex align-items-center">
                                <i class="fa fa-chevron-${open==='block' ? 'down' : 'right'} mr-2" id="wo-chevron-${safeId}"></i>
                                <span class="font-weight-bold">${utils.escapeHtml(wo.name)}</span>
                                ${pozLabel ? `<span class=\"badge badge-primary ml-2\" style=\"font-size:0.75rem;\">${utils.escapeHtml(pozLabel)}</span>` : ''}
                        </div>
                            <span class="badge badge-${statusBadge.class}" style="font-size:0.8rem;">${statusBadge.label}</span>
                        </div>
                        <div id="wo-body-${safeId}" style="display:${open};">
                            <div class="d-flex justify-content-between align-items-center p-2" style="border-bottom:1px solid #eee;">
                                <div><strong>Plan Başlangıç:</strong> ${utils.formatDate(wo.planned_start_date) || '-'}</div>
                                <div><strong>Plan Bitiş:</strong> ${utils.formatDate(wo.planned_end_date) || '-'}</div>
                                <div class="text-muted">Miktar: ${wo.qty || 0} | Üretilen: ${wo.produced_qty || 0}</div>
                            </div>
                            <div class="px-2 pt-2"><i class="fa fa-cogs mr-2"></i><strong>Operasyonlar</strong></div>
                            <div id="operations-content-${safeId}" class="p-2">
                                <div class="text-center p-2">
                                <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
                                    <span class="ml-2 text-muted">Operasyonlar yükleniyor...</span>
                            </div>
                        </div>
                    </div>
                    </div>`;
            }).join('')}
        </div>`;
            
        modalManager.updateModalContent(modalId, html);

    // Varsayılan olarak tüm iş emirleri kapalı; operasyonlar tıklanınca yüklenecek
}

function toggleWorkOrderSection(safeId, workOrderName) {
    const body = $(`#wo-body-${safeId}`);
    const chevron = $(`#wo-chevron-${safeId}`);
    if (!body.length) return;
    if (body.is(':visible')) {
        body.slideUp(200);
        chevron.removeClass('fa-chevron-down').addClass('fa-chevron-right');
    } else {
        body.slideDown(200);
        chevron.removeClass('fa-chevron-right').addClass('fa-chevron-down');
        // Lazy load operations if empty
        if (body.find('.operations-table').length === 0) {
            loadWorkOrderOperations(workOrderName, $(`#operations-content-${safeId}`));
        }
    }
}



// Helper function to get work order status badge
function getWorkOrderStatusBadge(status) {
    const statusMap = {
        'Draft': { label: 'Taslak', class: 'secondary' },
        'Not Started': { label: 'Başlamadı', class: 'warning' },
        'In Process': { label: 'İşlemde', class: 'primary' },
        'In Progress': { label: 'Devam Ediyor', class: 'primary' },
        'Pending': { label: 'Bekliyor', class: 'secondary' },
        'Completed': { label: 'Tamamlandı', class: 'success' },
        'Stopped': { label: 'Durduruldu', class: 'danger' },
        'Closed': { label: 'Kapatıldı', class: 'secondary' }
    };
    
    return statusMap[status] || { label: status || 'Bilinmiyor', class: 'secondary' };
}

// Helper function to calculate work order progress
function calculateWorkOrderProgress(wo) {
    const qty = parseFloat(wo.qty || 0);
    const producedQty = parseFloat(wo.produced_qty || 0);
    
    if (qty === 0) {
        return { percentage: 0, colorClass: 'bg-secondary' };
    }
    
    const percentage = (producedQty / qty) * 100;
    let colorClass = 'bg-info';
    
    if (percentage >= 100) colorClass = 'bg-success';
    else if (percentage >= 75) colorClass = 'bg-primary';
    else if (percentage >= 50) colorClass = 'bg-warning';
    else if (percentage >= 25) colorClass = 'bg-info';
    else colorClass = 'bg-danger';
    
    return { percentage: Math.min(percentage, 100), colorClass };
}

// Work order için poz/ürün etiketi belirleme
function getWorkOrderPozLabel(wo) {
    // Öncelik: production_item (Sales Order'daki alan), ardından sales_order_item, so_detail, poz_no
    const poz = wo.production_item || wo.sales_order_item || wo.so_detail || wo.poz_no || '';
    if (poz) return String(poz);
    const item = wo.item_name || wo.item_code || '';
    return item ? String(item) : '';
}

function showWorkOrderOperations(workOrderName) {
    const modalId = 'work-order-operations-' + Date.now();
    const cacheKey = `work-order-operations-${workOrderName}`;
    
    // Cache kontrolü
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        const modal = createModal(modalId, `İş Emri: ${workOrderName} - Operasyon Detayları`, 'modal-lg');
        setTimeout(() => {
            updateWorkOrderOperationsModal(cachedData.data, workOrderName, modalId);
        }, 100);
        return;
    }
    
    const modal = createModal(modalId, `İş Emri: ${workOrderName} - Operasyon Detayları`, 'modal-lg');
    
    // API çağrısı
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_work_order_operations_for_takip',
        args: { work_order_name: workOrderName },
        timeout: 15,
        callback: function(r) {
            if (r.exc) {
                showError('Operasyon detayları yüklenirken hata: ' + r.exc);
                modal.modal('hide');
                return;
            }
            
            const data = r.message;
            if (data.error) {
                showError(data.error);
                modal.modal('hide');
                return;
            }
            
            // Cache'e kaydet
            modalCache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            updateWorkOrderOperationsModal(data, workOrderName, modalId);
        }
    });
}



function toggleOperations(workOrderName) {
    const operationsContainer = $(`#operations-content-${workOrderName}`);
    const toggleBtn = $(`#toggle-btn-${workOrderName}`);
    const chevron = $(`#chevron-${workOrderName}`);
    
    if (!operationsContainer.length) {
        return;
    }
    
    if (operationsContainer.is(':visible')) {
        // Hide operations with smooth animation
        operationsContainer.slideUp(300);
        chevron.removeClass('fa-chevron-up').addClass('fa-chevron-down');
        toggleBtn.attr('title', 'Operasyonları göster');
    } else {
        // Show operations with smooth animation
        operationsContainer.slideDown(300);
        chevron.removeClass('fa-chevron-down').addClass('fa-chevron-up');
        toggleBtn.attr('title', 'Operasyonları gizle');
        
        // Load operations if not already loaded
        if (operationsContainer.find('.operations-table').length === 0) {
            loadWorkOrderOperations(workOrderName, operationsContainer);
        }
    }
}

function loadWorkOrderOperations(workOrderName, container) {
    if (!workOrderName || !container) {
                return;
            }
            
    // Show loading state
    container.html(`
        <div class="text-center p-3">
            <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
            <span class="ml-2">Operasyonlar yükleniyor...</span>
        </div>
    `);
    
    (async () => {
        try {
            const data = await apiService.call(
                'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_work_order_operations_for_takip',
                { work_order_name: workOrderName }
            );
            

            
            if (!data) {
                throw new Error('Operasyon verisi alınamadı');
            }
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            updateWorkOrderOperationsContent(data, container);
            
        } catch (error) {
            container.html(`
                <div class="alert alert-danger p-3">
                    <i class="fa fa-exclamation-triangle mr-2"></i>
                    <strong>Hata:</strong> ${utils.escapeHtml(error.message)}
                    <div class="mt-2">
                        <button class="btn btn-sm btn-primary" 
                                onclick="loadWorkOrderOperations('${workOrderName}', $('#operations-content-${workOrderName}'))">
                            <i class="fa fa-refresh mr-1"></i>Tekrar Dene
                        </button>
                    </div>
                </div>
            `);
        }
    })();
}

function updateWorkOrderOperationsContent(data, container) {
    const operations = data.operations || [];
    
    if (!operations || operations.length === 0) {
        container.html(`
            <div class="alert alert-info text-center">
                <i class="fa fa-info-circle mr-2"></i>
                Bu iş emri için operasyon bulunamadı
            </div>
        `);
        return;
    }
    
    const html = `
        <div class="operations-table">
            <div class="table-responsive">
                <table class="table table-sm table-hover mb-0">
                    <thead class="bg-light">
                        <tr>
                            <th>Operasyon</th>
                            <th>Durum</th>
                            <th>Tamamlanan</th>
                            <th>Planlanan Başlangıç</th>
                            <th>Planlanan Bitiş</th>
                            <th>Fiili Başlangıç</th>
                            <th>Fiili Bitiş</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${operations.map(op => {
                                    const statusBadge = getWorkOrderStatusBadge(op.status);
                                    const completedQty = parseFloat(op.completed_qty || 0);
                                    return `
                                <tr>
                                    <td><strong>${utils.escapeHtml(op.operation || '-')}</strong></td>
                                    <td><span class="badge badge-${statusBadge.class}">${statusBadge.label}</span></td>
                                    <td><span class="badge badge-success">${completedQty}</span></td>
                                    <td>${utils.formatDate(op.planned_start_time)}</td>
                                    <td>${utils.formatDate(op.planned_end_time)}</td>
                                    <td>${utils.formatDate(op.actual_start_time)}</td>
                                    <td>${utils.formatDate(op.actual_end_time)}</td>
                                </tr>`;
                                }).join('')}
                    </tbody>
                </table>
                    </div>
        </div>`;
    
    container.html(html);
}

function showWorkOrderStatus(workOrderName, currentStatus) {
    const statusOptions = {
        'Draft': 'Taslak',
        'Not Started': 'Başlamadı',
        'In Progress': 'Devam Ediyor',
        'Completed': 'Tamamlandı',
        'Stopped': 'Durduruldu',
        'Closed': 'Kapatıldı'
    };
    
    const modal = $(`
        <div class="modal fade" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fa fa-edit mr-2"></i>İş Emri Durumu Güncelle
                        </h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label><strong>İş Emri:</strong></label>
                            <p class="form-control-static">${workOrderName}</p>
                        </div>
                        <div class="form-group">
                            <label><strong>Mevcut Durum:</strong></label>
                            <span class="badge badge-${getWorkOrderStatusBadge(currentStatus).class}">${statusOptions[currentStatus] || currentStatus}</span>
                        </div>
                        <div class="form-group">
                            <label><strong>Yeni Durum:</strong></label>
                            <select id="newStatus" class="form-control">
                                ${Object.entries(statusOptions).map(([key, value]) => 
                                    `<option value="${key}" ${key === currentStatus ? 'selected' : ''}>${value}</option>`
                                ).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">İptal</button>
                        <button type="button" class="btn btn-primary" onclick="updateWorkOrderStatus('${workOrderName}')">
                            <i class="fa fa-save mr-1"></i>Güncelle
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    $('body').append(modal);
    modal.modal('show');
    
    modal.on('hidden.bs.modal', function() {
        $(this).remove();
    });
}

function updateWorkOrderStatus(workOrderName) {
    const newStatus = $('#newStatus').val();
    
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.update_work_order_status',
        args: { 
            work_order_name: workOrderName,
            new_status: newStatus
        },
        callback: function(r) {
            if (r.exc) {
                showError('Durum güncellenirken hata: ' + r.exc);
                return;
            }
            
            if (r.message && r.message.success) {
                showSuccess('İş emri durumu başarıyla güncellendi');
                $('.modal').modal('hide');
                // Tabloyu yenile
                loadProductionData();
            } else {
                showError('Durum güncellenirken hata oluştu');
            }
        }
    });
}



function showSuccess(message) {
    frappe.show_alert({
        message: message,
        indicator: 'green'
    }, 3);
}

function updateWorkOrderOperationsModal(data, workOrderName, modalId) {
    const content = $(`#modal-content-${modalId}`);
    
    // API'den gelen veriyi kontrol et
    const workOrder = data.work_order || {};
    const operations = data.operations || [];
    
    let html = `
        <!-- İş Emri Özet Tablosu -->
        <div class="card mb-3">
            <div class="card-header bg-light">
                <i class="fa fa-info-circle mr-2"></i>İş Emri Bilgileri
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="bg-warning text-dark">
                            <tr>
                                <th>İş Emri</th>
                                <th>Durum</th>
                                <th>Miktar</th>
                                <th>Üretilen</th>
                                <th>Planlanan Başlangıç</th>
                                <th>Planlanan Bitiş</th>
                            </tr>
                        </thead>
                        <tbody>
                                            <tr>
                    <td>
                        <div class="d-flex align-items-center">
                            <span class="font-weight-bold">${workOrder.name || workOrderName}</span>
                        </div>
                    </td>
                    <td>
                        <span class="badge badge-${getWorkOrderStatusBadge(workOrder.status).class}">${getWorkOrderStatusBadge(workOrder.status).label}</span>
                    </td>
                    <td>
                        <span class="badge badge-info">${workOrder.qty || 0}</span>
                    </td>
                    <td>
                        <span class="badge badge-success">${workOrder.produced_qty || 0}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${utils.formatDate(workOrder.planned_start_date)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${utils.formatDate(workOrder.planned_end_date)}</span>
                    </td>
                </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Operasyonlar Tablosu -->
        <div class="card">
            <div class="card-header bg-light">
                <i class="fa fa-cogs mr-2"></i>Operasyonlar
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="bg-primary text-white">
                            <tr>
                                <th>Operasyon</th>
                                <th>Durum</th>
                                <th>Tamamlanan</th>
                                <th>Planlanan Başlangıç</th>
                                <th>Planlanan Bitiş</th>
                                <th>Fiili Başlangıç</th>
                                <th>Fiili Bitiş</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    if (operations && operations.length > 0) {
        operations.forEach((op, index) => {
            const statusBadge = getWorkOrderStatusBadge(op.status);
            
            html += `
                <tr>
                    <td>
                        <strong>${op.operation || '-'}</strong>
                    </td>
                    <td>
                        <span class="badge badge-${statusBadge.class}">${statusBadge.label}</span>
                    </td>
                    <td>
                        <span class="badge badge-success">${op.completed_qty || 0}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${utils.formatDate(op.planned_start_time)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${utils.formatDate(op.planned_end_time)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${utils.formatDate(op.actual_start_time)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${utils.formatDate(op.actual_end_time)}</span>
                    </td>
                </tr>
            `;
        });
    } else {
        html += '<tr><td colspan="8" class="text-center text-muted">Operasyon bulunamadı</td></tr>';
    }
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    content.html(html);
}



// Yeni modal fonksiyonları
function showProductionPlan(planName) {
    const modal = $(`
        <div class="modal fade" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fa fa-calendar mr-2"></i>Üretim Planı: ${planName}
                        </h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div id="production-plan-content">
                            <div class="text-center">
                                <div class="spinner-border" role="status"></div>
                                <p>Üretim planı detayları yükleniyor...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    modal.modal('show');
    
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_production_plan_details',
        args: { plan_name: planName },
        callback: function(r) {
            if (r.exc) {
                showError('Üretim planı detayları yüklenirken hata: ' + r.exc);
                return;
            }
            
            const data = r.message;
            if (data.error) {
                showError(data.error);
                return;
            }
            
            updateProductionPlanModal(data);
        }
    });
}

function showItemDetails(itemCode) {
    const modal = $(`
        <div class="modal fade" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title">
                            <i class="fa fa-cube mr-2"></i>Ürün: ${itemCode}
                        </h5>
                        <button type="button" class="close text-white" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div id="item-details-content">
                            <div class="text-center">
                                <div class="spinner-border" role="status"></div>
                                <p>Ürün detayları yükleniyor...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    modal.modal('show');
    
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_item_details_for_takip',
        args: { item_code: itemCode },
        callback: function(r) {
            if (r.exc) {
                showError('Ürün detayları yüklenirken hata: ' + r.exc);
                return;
            }
            
            const data = r.message;
            if (data.error) {
                showError(data.error);
                return;
            }
            
            updateItemDetailsModal(data);
        }
    });
}

function updateProductionPlanModal(data) {
    const content = $('#production-plan-content');
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fa fa-info-circle mr-2"></i>Plan Bilgileri</h6>
                <table class="table table-sm table-bordered">
                    <tr><td><strong>Plan Adı:</strong></td><td><span class="badge badge-primary">${data.name}</span></td></tr>
                    <tr><td><strong>Durum:</strong></td><td><span class="badge badge-${getWorkOrderStatusBadge(data.status).class}">${getWorkOrderStatusBadge(data.status).label}</span></td></tr>
                    <tr><td><strong>Planlanan Başlangıç:</strong></td><td>${utils.formatDate(data.planned_start_date)}</td></tr>
                    <tr><td><strong>Planlanan Bitiş:</strong></td><td>${utils.formatDate(data.planned_end_date)}</td></tr>
                    <tr><td><strong>Gerçek Başlangıç:</strong></td><td>${utils.formatDate(data.actual_start_date)}</td></tr>
                    <tr><td><strong>Gerçek Bitiş:</strong></td><td>${utils.formatDate(data.actual_end_date)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="fa fa-calculator mr-2"></i>Özet</h6>
                <table class="table table-sm table-bordered">
                    <tr><td><strong>Toplam Sipariş:</strong></td><td><span class="badge badge-info">${data.total_orders}</span></td></tr>
                    <tr><td><strong>Toplam Miktar:</strong></td><td><span class="badge badge-success">${data.total_qty}</span></td></tr>
                    <tr><td><strong>Üretilen:</strong></td><td><span class="badge badge-warning">${data.produced_qty}</span></td></tr>
                    <tr><td><strong>İlerleme:</strong></td><td>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-success" style="width: ${data.progress_percentage}%">
                                ${data.progress_percentage}%
                            </div>
                        </div>
                    </td></tr>
                </table>
            </div>
        </div>
    `;
    
    content.html(html);
}

function updateItemDetailsModal(data) {
    const content = $('#item-details-content');
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fa fa-cube mr-2"></i>Ürün Bilgileri</h6>
                <table class="table table-sm table-bordered">
                    <tr><td><strong>Ürün Kodu:</strong></td><td><span class="badge badge-primary">${data.item_code}</span></td></tr>
                    <tr><td><strong>Ürün Adı:</strong></td><td>${data.item_name}</td></tr>
                    <tr><td><strong>Ürün Grubu:</strong></td><td><span class="badge badge-info">${data.item_group}</span></td></tr>
                    <tr><td><strong>Seri:</strong></td><td>${data.seri || '-'}</td></tr>
                    <tr><td><strong>Renk:</strong></td><td>${data.renk || '-'}</td></tr>
                    <tr><td><strong>Stok Türü:</strong></td><td>${data.stok_turu || '-'}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="fa fa-calculator mr-2"></i>Teknik Bilgiler</h6>
                <table class="table table-sm table-bordered">
                    <tr><td><strong>MTÜL/m²:</strong></td><td><span class="badge badge-success">${data.mtul_per_piece || 0}</span></td></tr>
                    <tr><td><strong>Toplam Ana Profil MTÜL:</strong></td><td><span class="badge badge-warning">${data.total_main_profiles_mtul || 0}</span></td></tr>
                    <tr><td><strong>Uzunluk:</strong></td><td>${data.length || '-'}</td></tr>
                    <tr><td><strong>Genişlik:</strong></td><td>${data.width || '-'}</td></tr>
                    <tr><td><strong>Yükseklik:</strong></td><td>${data.height || '-'}</td></tr>
                    <tr><td><strong>Ağırlık:</strong></td><td>${data.weight || '-'}</td></tr>
                </table>
            </div>
        </div>
    `;
    
    content.html(html);
} 