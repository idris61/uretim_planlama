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
    max-width: 95%;
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

// Global değişkenler
let allPlannedData = [];
let showCompletedItems = false;
let lastUpdate = 0;
let updateInterval = null;
let debounceTimer = null;

// Performans optimizasyonları
let dataCache = new Map();
let lastCacheUpdate = 0;
const CACHE_DURATION = 30000; // 30 saniye
const DATA_LOAD_TIMEOUT = 10000; // 10 saniye timeout

// Modal performans optimizasyonları
let activeModals = new Set();
let modalCache = new Map();
const MODAL_CACHE_DURATION = 60000; // 1 dakika

// Modal yönetimi fonksiyonları
function closeAllModals() {
    $('.modal').modal('hide');
    setTimeout(() => {
        $('.modal').remove();
        activeModals.clear();
    }, 300);
}

function closeOtherModals(currentModalId) {
    $('.modal').not(`#${currentModalId}`).modal('hide');
    setTimeout(() => {
        $('.modal').not(`#${currentModalId}`).remove();
    }, 300);
}

function createModal(modalId, title, size = 'modal-lg') {
    console.log('Creating modal with ID:', modalId);
    
    // Sadece eski modalları kapat, yeni modal'ı etkileme
    closeOtherModals(modalId);
    
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1" data-backdrop="static" data-keyboard="false">
            <div class="modal-dialog ${size}">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fa fa-spinner fa-spin mr-2"></i>${title}
                        </h5>
                        <button type="button" class="close text-white" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                                                    <div class="modal-body" style="max-height: 70vh; overflow-y: scroll;">
                        <div id="modal-content-${modalId}" class="modal-content-inner">
                            <div class="text-center p-4">
                                <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                                <p class="mt-2 text-muted">Yükleniyor...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    try {
        $('body').append(modalHtml);
        const modal = $(`#${modalId}`);
        
        if (!modal.length) {
            console.error('Modal element not found after creation:', modalId);
            return null;
        }
        
        modal.on('hidden.bs.modal', function() {
            $(this).remove();
            activeModals.delete(modalId);
        });
        
        activeModals.add(modalId);
        modal.modal('show');
        
        // Modal'ın DOM'da olduğunu kontrol et
        setTimeout(() => {
            const modalExists = $(`#${modalId}`).length > 0;
            const contentElement = $(`#modal-content-${modalId}`);
            console.log('Modal exists in DOM:', modalExists);
            console.log('Content element exists:', contentElement.length > 0);
        }, 100);
        
        console.log('Modal created successfully:', modalId);
        
        return modal;
    } catch (error) {
        console.error('Error creating modal:', error);
        return null;
    }
}

function createPageStructure(container) {
    container.html(`
        <div class="container-fluid">
            <!-- Header Section -->
            <div class="row mb-3">
                <div class="col-12">
                    <div class="d-flex align-items-center">
                        <button type="button" id="refreshBtn" class="btn btn-dark btn-sm mr-3">
                            <i class="fa fa-refresh"></i> Verileri Yenile
                        </button>
                        <button type="button" id="clearCacheBtn" class="btn btn-warning btn-sm mr-3">
                            <i class="fa fa-trash"></i> Cache Temizle
                        </button>
                        <span class="text-muted" id="lastUpdate">Son güncelleme: --:--:-- (0 kayıt)</span>
                    </div>
                </div>
            </div>
            
            <!-- Özet Kartları -->
            <div id="summary-cards" class="row mb-4">
                <!-- Üretim Plan Verileri -->
                <div class="col-12 mb-3">
                    <h6 class="text-muted mb-2"><i class="fa fa-industry mr-1"></i>Üretim Plan Verileri</h6>
                    <div class="row" id="production-cards"></div>
                </div>
                <!-- Satış Sipariş Verileri -->
                <div class="col-12">
                    <h6 class="text-muted mb-2"><i class="fa fa-shopping-cart mr-1"></i>Satış Sipariş Verileri</h6>
                    <div class="row" id="order-cards"></div>
                </div>
            </div>
            
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
                                    <th style="width: 8%;">BAŞLANGIÇ</th>
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
    
    // Yenile butonu
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => loadProductionData());
    }
    
    // Cache temizleme butonu
    const clearCacheBtn = document.getElementById('clearCacheBtn');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', () => clearCache());
    }
}

function loadProductionData() {
    const now = Date.now();
    if (now - lastUpdate < 1000) {
        return;
    }
    
    // Cache kontrolü
    const cacheKey = JSON.stringify(getFilters());
    const cachedData = dataCache.get(cacheKey);
    if (cachedData && (now - cachedData.timestamp) < CACHE_DURATION) {
        allPlannedData = cachedData.data;
        updateSummary();
        renderPlannedTable();
        updateCompletedToggle();
        return;
    }
    
    showLoading();
    lastUpdate = now;
    
    const filters = getFilters();
    
    // Timeout ile API çağrısı
    const apiCall = frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_production_planning_data',
        args: { filters: JSON.stringify(filters) },
        timeout: DATA_LOAD_TIMEOUT,
        callback: function(r) {
            hideLoading();
            
            if (r.exc) {
                console.error('❌ API hatası:', r.exc);
                showError('Veri yüklenirken hata: ' + r.exc);
                return;
            }
            
            const data = r.message;
            
            if (data.error) {
                console.error('❌ Veri hatası:', data.error);
                showError(data.error);
                return;
            }
            
            allPlannedData = data.planned || [];
            
            // Cache'e kaydet
            dataCache.set(cacheKey, {
                data: allPlannedData,
                timestamp: now
            });
            
            updateSummary();
            renderPlannedTable();
            updateCompletedToggle();
        },
        error: function(err) {
            hideLoading();
            showError('Bağlantı hatası: ' + err);
        }
    });

    // Timeout kontrolü
    setTimeout(() => {
        if ($('#loadingSpinner').is(':visible')) {
            hideLoading();
            showError('Veri yükleme zaman aşımı. Lütfen tekrar deneyin.');
        }
    }, DATA_LOAD_TIMEOUT + 1000);
}

function getFilters() {
    const showCompletedToggle = document.getElementById('showCompletedToggle');
    return {
        optiNo: document.getElementById('optiNoFilter')?.value || '',
        siparisNo: document.getElementById('siparisNoFilter')?.value || '',
        bayi: document.getElementById('bayiFilter')?.value || '',
        musteri: document.getElementById('musteriFilter')?.value || '',
        seri: document.getElementById('seriFilter')?.value || '',
        renk: document.getElementById('renkFilter')?.value || '',
        uretimTipi: document.getElementById('durumFilter')?.value || 'tumu',
        durum: document.getElementById('durumFilter')?.value || 'tumu',
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
        console.error('❌ plannedTableBody bulunamadı');
        return;
    }
    
    if (!allPlannedData || allPlannedData.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="14" class="text-center text-muted">
                <i class="fa fa-info-circle mr-2"></i>Henüz planlama bulunmuyor
            </td></tr>
        `;
        return;
    }
    
    // Filtreleri al
    const filters = getFilters();
    
    // Tamamlananları göster/gizle filtresi
    let filteredData = allPlannedData;
    if (!filters.showCompleted) {
        filteredData = allPlannedData.filter(item => item.plan_status !== 'Completed');
    }
    
    // Performans için sadece ilk 200 kayıt
    if (filteredData.length > 200) {
        filteredData = filteredData.slice(0, 200);
        console.warn('⚠️ Performans için sadece ilk 200 kayıt gösteriliyor');
    }
    
    // Opti numarasına göre gruplandır
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
                seri: order.seri,
                renk: order.renk,
                plan_status: order.plan_status
            };
        }
        optiGroups[optiNo].sales_orders.push(order.sales_order);
        optiGroups[optiNo].total_pvc += order.pvc_count || 0;
        optiGroups[optiNo].total_cam += order.cam_count || 0;
        optiGroups[optiNo].total_mtul += order.toplam_mtul_m2 || 0;
    });
    
    // Sıralama: Tamamlananlar üstte, sonra planlama tarihine göre
    const sortedOptiGroups = Object.values(optiGroups).sort((a, b) => {
        // Önce tamamlanan durumuna göre sırala (tamamlananlar üstte)
        const aCompleted = a.plan_status === 'Completed';
        const bCompleted = b.plan_status === 'Completed';
        
        if (aCompleted && !bCompleted) return -1;
        if (!aCompleted && bCompleted) return 1;
        
        // Sonra planlama tarihine göre sırala (eski tarihler üstte)
        const aDate = new Date(a.planlanan_baslangic_tarihi || '1900-01-01');
        const bDate = new Date(b.planlanan_baslangic_tarihi || '1900-01-01');
        
        return aDate - bDate;
    });
    
    // Performans için DocumentFragment kullan
    const fragment = document.createDocumentFragment();
    
    sortedOptiGroups.forEach((optiGroup, index) => {
        const optiRow = createOptiRowElement(optiGroup);
        fragment.appendChild(optiRow);
    });
    
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
    bindTableEvents();
}





function createOptiRowElement(optiGroup) {
    const row = document.createElement('tr');
    const rowClass = getRowClass(optiGroup.total_pvc || 0, optiGroup.total_cam || 0);
    const isUrgent = isUrgentDelivery(optiGroup.bitis_tarihi);
    const urgentClass = isUrgent ? 'urgent-delivery' : '';
    const isCompleted = optiGroup.plan_status === 'Completed';
    
    // Tamamlanan satırlar için completed-row class'ını öncelikli yap
    if (isCompleted) {
        row.className = `completed-row opti-row ${urgentClass}`;
    } else {
        row.className = `${rowClass} ${urgentClass} opti-row`;
    }
    row.dataset.opti = optiGroup.opti_no;
    
    // Müşteri adını kısalt
    const musteriText = optiGroup.musteri || '-';
    const truncatedMusteri = musteriText.length > 25 ? musteriText.substring(0, 22) + '...' : musteriText;
    
    // Sipariş numaralarını birleştir
    const siparisText = optiGroup.sales_orders.join(', ');
    const truncatedSiparis = siparisText.length > 20 ? siparisText.substring(0, 17) + '...' : siparisText;
    
    row.innerHTML = `
        <td class="text-center">
            <span class="badge badge-info">${optiGroup.hafta || '-'}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-primary">${optiGroup.opti_no}</span>
        </td>
        <td title="${siparisText}">
            <span class="font-weight-bold text-primary">${truncatedSiparis}</span>
        </td>
        <td title="${optiGroup.bayi || '-'}">${(optiGroup.bayi || '-').length > 15 ? (optiGroup.bayi || '-').substring(0, 12) + '...' : (optiGroup.bayi || '-')}</td>
        <td title="${musteriText}">${truncatedMusteri}</td>
        <td class="text-center">
            <span class="badge badge-warning">${formatDate(optiGroup.siparis_tarihi)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-danger">${formatDate(optiGroup.bitis_tarihi)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-danger">${optiGroup.total_pvc || 0}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-primary">${optiGroup.total_cam || 0}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-success">${(optiGroup.total_mtul || 0).toFixed(2)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-warning">${formatDate(optiGroup.planlanan_baslangic_tarihi)}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-info">${optiGroup.seri || '-'}</span>
        </td>
        <td class="text-center">
            <span class="badge badge-warning">${optiGroup.renk || '-'}</span>
        </td>
    `;
    
    return row;
}

function getRowClass(pvcCount, camCount) {
    if (pvcCount > 0 && camCount > 0) return 'mixed-row';
    if (pvcCount > 0) return 'pvc-row';
    if (camCount > 0) return 'cam-row';
    return 'default-row';
}

function getStatusBadge(status) {
    const statusMap = {
        'Completed': 'success',
        'In Process': 'warning',
        'Not Started': 'secondary',
        'Stopped': 'danger',
        'Closed': 'info'
    };
    
    const badgeClass = statusMap[status] || 'secondary';
    const statusText = getStatusText(status);
    
    return `<span class="badge badge-${badgeClass}">${statusText}</span>`;
}

function getStatusText(status) {
    const statusTextMap = {
        'Completed': 'Tamamlandı',
        'In Process': 'Devam Ediyor',
        'Not Started': 'Başlamadı',
        'Stopped': 'Durduruldu',
        'Closed': 'Kapatıldı'
    };
    
    return statusTextMap[status] || status;
}

function getStatusClass(status) {
    const statusClassMap = {
        'Completed': 'success',
        'In Process': 'warning',
        'Not Started': 'secondary',
        'Stopped': 'danger',
        'Closed': 'info'
    };
    
    return statusClassMap[status] || 'secondary';
}

function getStatusBadge(status) {
    const statusMap = {
        'Completed': 'success',
        'In Process': 'warning',
        'Not Started': 'secondary'
    };
    
    const badgeClass = statusMap[status] || 'secondary';
    const statusText = getStatusText(status);
    
    return `<span class="badge badge-${badgeClass}">${statusText}</span>`;
}

function getStatusText(status) {
    const statusTextMap = {
        'Completed': 'Tamamlandı',
        'In Process': 'Devam Ediyor',
        'Not Started': 'Başlamadı'
    };
    
    return statusTextMap[status] || status;
}

function isUrgentDelivery(deliveryDate) {
    if (!deliveryDate) return false;
    
    try {
        const delivery = new Date(deliveryDate);
        const today = new Date();
        return delivery < today;
    } catch {
        return false;
    }
}

function updateSummary() {
    const productionCards = document.getElementById('production-cards');
    const orderCards = document.getElementById('order-cards');
    if (!productionCards || !orderCards || !allPlannedData) return;
    
    // Opti numarasına göre gruplandır
    const optiGroups = {};
    allPlannedData.forEach(order => {
        const optiNo = order.opti_no;
        if (!optiGroups[optiNo]) {
            optiGroups[optiNo] = {
                opti_no: optiNo,
                plan_status: order.plan_status,
                orders: []
            };
        }
        optiGroups[optiNo].orders.push(order);
    });
    
    const totalOpti = Object.keys(optiGroups).length;
    const totalSiparis = allPlannedData.length;
    const completedOpti = Object.values(optiGroups).filter(opti => opti.plan_status === 'Completed').length;
    const ongoingOpti = totalOpti - completedOpti;
    const completedSiparis = allPlannedData.filter(item => item.plan_status === 'Completed').length;
    const ongoingSiparis = totalSiparis - completedSiparis;
    
    // Üretim Plan Kartları
    productionCards.innerHTML = `
        <div class="col-md-4 mb-2">
            <div class="card summary-card" style="background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%); color: white;">
                <div class="card-body text-center p-3">
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fa fa-industry mr-2" style="font-size: 1.2rem;"></i>
                        <div>
                            <h5 class="mb-0" style="font-size: 0.9rem;">Planlanan Üretim</h5>
                            <h4 class="mb-0" style="font-size: 1.4rem;">${totalOpti}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-2">
            <div class="card summary-card" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white;">
                <div class="card-body text-center p-3">
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fa fa-check-circle mr-2" style="font-size: 1.2rem;"></i>
                        <div>
                            <h5 class="mb-0" style="font-size: 0.9rem;">Tamamlanan Üretim</h5>
                            <h4 class="mb-0" style="font-size: 1.4rem;">${completedOpti}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-2">
            <div class="card summary-card" style="background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%); color: white;">
                <div class="card-body text-center p-3">
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fa fa-clock-o mr-2" style="font-size: 1.2rem;"></i>
                        <div>
                            <h5 class="mb-0" style="font-size: 0.9rem;">Devam Eden Üretim</h5>
                            <h4 class="mb-0" style="font-size: 1.4rem;">${ongoingOpti}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Satış Sipariş Kartları
    orderCards.innerHTML = `
        <div class="col-md-4 mb-2">
            <div class="card summary-card" style="background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%); color: white;">
                <div class="card-body text-center p-3">
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fa fa-shopping-cart mr-2" style="font-size: 1.2rem;"></i>
                        <div>
                            <h5 class="mb-0" style="font-size: 0.9rem;">Planlanan Sipariş</h5>
                            <h4 class="mb-0" style="font-size: 1.4rem;">${totalSiparis}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-2">
            <div class="card summary-card" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white;">
                <div class="card-body text-center p-3">
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fa fa-check-circle mr-2" style="font-size: 1.2rem;"></i>
                        <div>
                            <h5 class="mb-0" style="font-size: 0.9rem;">Tamamlanan Sipariş</h5>
                            <h4 class="mb-0" style="font-size: 1.4rem;">${completedSiparis}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-2">
            <div class="card summary-card" style="background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%); color: white;">
                <div class="card-body text-center p-3">
                    <div class="d-flex align-items-center justify-content-center">
                        <i class="fa fa-clock-o mr-2" style="font-size: 1.2rem;"></i>
                        <div>
                            <h5 class="mb-0" style="font-size: 0.9rem;">Devam Eden Sipariş</h5>
                            <h4 class="mb-0" style="font-size: 1.4rem;">${ongoingSiparis}</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Planlanan sayısını güncelle (üretim planı sayısı)
    const planlananCount = document.getElementById('planlanan-count');
    if (planlananCount) {
        planlananCount.textContent = totalOpti;
    }
    
    // Son güncelleme zamanını güncelle
    const lastUpdate = document.getElementById('lastUpdate');
    if (lastUpdate) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('tr-TR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        lastUpdate.textContent = `Son güncelleme: ${timeStr} (${totalOpti} kayıt)`;
    }
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

function debouncedApplyFilters() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
    
        loadProductionData();
    }, 300);
}

function startAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    
    updateInterval = setInterval(() => {
        if (!document.hidden && !document.querySelector('.modal.show')) {
        
            loadProductionData();
        }
    }, 30000); // 30 saniyede bir güncelle
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
    document.querySelectorAll('#plannedTableBody tr[data-opti]').forEach(row => {
        row.addEventListener('click', (e) => {
            if (!e.target.closest('button') && !e.target.closest('a')) {
                showOptiDetails(row.dataset.opti);
            }
        });
    });
}

function showLoading() {
    // Loading overlay'i gizli yap - kullanıcı fark etmesin
}

function hideLoading() {
    // Loading overlay'i gizli yap - kullanıcı fark etmesin
}

function showError(message, title = 'Hata') {
    console.error('❌ Hata:', message);
    
    // Toast notification göster
    frappe.show_alert({
        message: message,
        indicator: 'red'
    }, 5);
    
    // Detaylı hata modal'ı
    if (message.includes('API') || message.includes('network')) {
        const modal = $(`
            <div class="modal fade" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fa fa-exclamation-triangle mr-2"></i>${title}
                            </h5>
                            <button type="button" class="close text-white" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger">
                                <i class="fa fa-exclamation-circle mr-2"></i>
                                <strong>Hata Detayı:</strong><br>
                                ${message}
                            </div>
                            <div class="mt-3">
                                <button class="btn btn-primary" onclick="loadProductionData()">
                                    <i class="fa fa-refresh mr-2"></i>Tekrar Dene
                                </button>
                                <button class="btn btn-secondary ml-2" onclick="clearCache()">
                                    <i class="fa fa-trash mr-2"></i>Cache Temizle
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        modal.modal('show');
    }
}

// Cache temizleme
function clearCache() {
    dataCache.clear();
    modalCache.clear();
    lastCacheUpdate = 0;
    activeModals.clear();
    closeAllModals();
    
    frappe.show_alert('Tüm cache temizlendi', 'green');
}

// Modal fonksiyonları
function showOptiDetails(optiNo) {
    const modal = $(`
        <div class="modal fade" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fa fa-cogs mr-2"></i>Opti ${optiNo} - Sipariş Detayları
                        </h5>
                        <button type="button" class="close text-white" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body p-0">
                        <div id="opti-details-content">
                            <div class="text-center p-4">
                                <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);
    
    modal.modal('show');
    
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_opti_details_for_takip',
        args: { opti_no: optiNo },
        callback: function(r) {
                    if (r.exc) {
                showError('Opti detayları yüklenirken hata: ' + r.exc);
                        return;
                    }
                    
            const data = r.message;
            if (data.error) {
                showError(data.error);
                return;
            }
            
            updateOptiDetailsModal(data);
        }
    });
}

function showOrderDetails(salesOrder) {
    const modalId = 'order-details-' + Date.now();
    const cacheKey = `order-details-${salesOrder}`;
    
    // Cache kontrolü
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        const modal = createModal(modalId, `Sipariş: ${salesOrder}`, 'modal-lg');
        setTimeout(() => {
            updateOrderDetailsModal(cachedData.data, modalId);
        }, 100);
        return;
    }
    
    const modal = createModal(modalId, `Sipariş: ${salesOrder}`, 'modal-lg');
    
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

function showWorkOrders(salesOrder) {
    console.log('showWorkOrders called with salesOrder:', salesOrder);
    
    const modalId = 'work-orders-' + Date.now();
    const cacheKey = `work-orders-${salesOrder}`;
    
    // Cache kontrolü
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        console.log('Using cached data for work orders');
        const modal = createModal(modalId, `İş Emirleri Detayları`, 'modal-lg');
        if (modal) {
            // Modal content element'inin varlığını kontrol et
            const contentElement = $(`#modal-content-${modalId}`);
            if (contentElement.length) {
                            setTimeout(() => {
                updateWorkOrdersModal(cachedData.data, modalId, salesOrder);
            }, 100);
            } else {
                console.error('Modal content element not found in cache mode');
            }
        }
        return;
    }
    
            const modal = createModal(modalId, `İş Emirleri Detayları`, 'modal-lg');
    if (!modal) {
        showError('Modal oluşturulamadı');
        return;
    }
    
    // Modal content element'inin varlığını kontrol et
    const contentElement = $(`#modal-content-${modalId}`);
    if (!contentElement.length) {
        console.error('Modal content element not found after creation');
        showError('Modal içeriği oluşturulamadı');
        return;
    }
    
    // API çağrısı
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_work_orders_for_takip',
        args: { sales_order: salesOrder },
        timeout: 30,
        callback: function(r) {
            console.log('API Response:', r);
            console.log('API Response message:', r.message);
            console.log('API Response type:', typeof r.message);
            
            if (r.exc) {
                console.error('API Error:', r.exc);
                showError('İş emirleri yüklenirken hata: ' + r.exc);
                modal.modal('hide');
                return;
            }
            
            const data = r.message;
            console.log('Work Orders Data:', data);
            console.log('Data length:', data ? data.length : 'undefined');
            console.log('Data type:', Array.isArray(data) ? 'Array' : typeof data);
            
            if (!data) {
                showError('İş emirleri verisi alınamadı');
                modal.modal('hide');
                return;
            }
            
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
            
            updateWorkOrdersModal(data, modalId, salesOrder);
        },
        error: function(err) {
            console.error('Network Error:', err);
            showError('Bağlantı hatası: ' + err);
            modal.modal('hide');
        }
    });
}

function updateOptiDetailsModal(data) {
    const content = $('#opti-details-content');
    
    let html = `
        <div class="alert alert-info">
            <i class="fa fa-info-circle mr-2"></i>
            <strong>Opti ${data.opti_no}</strong> - Toplam ${data.orders.length} sipariş planlandı
        </div>
        
        <div class="row mb-3">
            <div class="col-md-4">
                <div class="card bg-danger text-white">
                    <div class="card-body text-center">
                        <h3 class="mb-0">${data.summary.total_pvc}</h3>
                        <small>Toplam Profil</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h3 class="mb-0">${data.summary.total_cam}</h3>
                        <small>Toplam Cam</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h3 class="mb-0">${data.summary.total_mtul.toFixed(2)}</h3>
                        <small>Toplam MTÜL/m²</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header bg-light">
                <i class="fa fa-list mr-2"></i>Sipariş Detayları
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="bg-info text-white">
                            <tr>
                                <th>Sipariş No</th>
                                <th>Bayi</th>
                                <th>Müşteri</th>
                                <th>Seri</th>
                                <th>Renk</th>
                                <th>Adet</th>
                                <th>MTÜL/m²</th>
                                <th>Durum & Açıklama</th>
                                <th>İşlemler</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    data.orders.forEach(order => {
        const orderDate = formatDate(order.siparis_tarihi);
        const statusText = getStatusText(order.uretim_plani_durumu);
        const statusClass = getStatusClass(order.uretim_plani_durumu);
        const description = order.siparis_aciklama || 'Açıklama yok';
        
        // Acil durumu kontrol et
        const isUrgent = order.is_urgent || order.urgent || false;
        const urgencyBadge = isUrgent ? 
            '<span class="badge badge-danger mr-1"><i class="fa fa-exclamation-triangle"></i> ACİL</span>' : 
            '<span class="badge badge-secondary mr-1"><i class="fa fa-check-circle"></i> NORMAL</span>';
        
        html += `
            <tr>
                <td>
                    <div class="d-flex flex-column">
                        <span class="badge badge-info mb-1">${order.sales_order}</span>
                        <small class="text-muted">${orderDate}</small>
                    </div>
                </td>
                <td class="text-muted">${order.bayi || '-'}</td>
                <td class="text-muted">${order.musteri}</td>
                <td>
                    <span class="badge badge-info">${order.seri || '-'}</span>
                </td>
                <td>
                    <span class="badge badge-warning">${order.renk || '-'}</span>
                </td>
                <td>
                    ${order.pvc_qty > 0 ? `<span class="badge badge-danger d-block mb-1">${order.pvc_qty} Profil</span>` : ''}
                    ${order.cam_qty > 0 ? `<span class="badge badge-primary d-block">${order.cam_qty} Cam</span>` : ''}
                </td>
                <td>
                    <span class="badge badge-success">${order.total_mtul.toFixed(2)}</span>
                </td>
                <td>
                    <div class="d-flex flex-column">
                        <div class="mb-1">
                            ${urgencyBadge}
                            <span class="badge badge-${statusClass}">✔ ${statusText}</span>
                        </div>
                        <small class="text-muted">${description}</small>
                    </div>
                </td>
                <td>
                    <div class="d-flex flex-column">
                        <a href="/app/sales-order/${order.sales_order}" target="_blank" class="btn btn-sm btn-outline-primary mb-1">
                            <i class="fa fa-external-link mr-1"></i>Sipariş
                        </a>
                        <button class="btn btn-sm btn-outline-success" onclick="showWorkOrders('${order.sales_order}')">
                            <i class="fa fa-bars mr-1"></i>İş Emirleri
                        </button>
                    </div>
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
    
    content.html(html);
}

function updateOrderDetailsModal(data, modalId) {
    const content = $(`#modal-content-${modalId}`);
    
    // Satış siparişinin acil durumunu kontrol et
    const isUrgent = data.acil || false;
    const urgencyStatus = isUrgent ? 
        '<span class="badge badge-danger"><i class="fa fa-exclamation-triangle mr-1"></i>ACİL</span>' : 
        '<span class="badge badge-secondary"><i class="fa fa-check-circle mr-1"></i>NORMAL</span>';
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fa fa-shopping-cart mr-2"></i>Sipariş Bilgileri</h6>
                <table class="table table-sm table-bordered">
                    <tr><td><strong>Sipariş No:</strong></td><td><span class="badge badge-primary">${data.sales_order}</span></td></tr>
                    <tr><td><strong>Bayi:</strong></td><td>${data.bayi || '-'}</td></tr>
                    <tr><td><strong>Müşteri:</strong></td><td>${data.musteri || '-'}</td></tr>
                    <tr><td><strong>Sipariş Tarihi:</strong></td><td>${formatDate(data.siparis_tarihi)}</td></tr>
                    <tr><td><strong>Teslim Tarihi:</strong></td><td>${formatDate(data.bitis_tarihi)}</td></tr>
                    <tr><td><strong>Öncelik:</strong></td><td>${urgencyStatus}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="fa fa-cogs mr-2"></i>Üretim Bilgileri</h6>
                <table class="table table-sm table-bordered">
                    <tr><td><strong>Opti No:</strong></td><td><span class="badge badge-warning">${data.opti_no || '-'}</span></td></tr>
                    <tr><td><strong>Seri:</strong></td><td>${data.seri || '-'}</td></tr>
                    <tr><td><strong>Renk:</strong></td><td>${data.renk || '-'}</td></tr>
                    <tr><td><strong>PVC:</strong></td><td><span class="badge badge-danger">${data.pvc_count || 0}</span></td></tr>
                    <tr><td><strong>Cam:</strong></td><td><span class="badge badge-primary">${data.cam_count || 0}</span></td></tr>
                    <tr><td><strong>Toplam MTÜL:</strong></td><td><span class="badge badge-success">${(data.toplam_mtul || 0).toFixed(2)}</span></td></tr>
                </table>
            </div>
        </div>
        
        ${data.aciklama ? `
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fa fa-comment mr-2"></i>Açıklama</h6>
                <div class="alert alert-info">
                    ${data.aciklama}
                </div>
            </div>
        </div>
        ` : ''}
    `;
    
    content.html(html);
}

function updateWorkOrdersModal(data, modalId, salesOrder) {
    console.log('Updating Work Orders Modal with data:', data);
    
    // Modal content element'ini bul
    let content = $(`#modal-content-${modalId}`);
    if (!content.length) {
        content = $(`#${modalId}`).find('.modal-content-inner');
    }
    
    if (!content.length) {
        console.error('Modal content element not found');
        return;
    }
    
    let html = `
        <div class="mb-3">
            <h6 class="text-muted">
                <i class="fa fa-shopping-cart mr-2"></i>Sipariş No: ${salesOrder}
            </h6>
        </div>
    `;
    
    if (data && Array.isArray(data) && data.length > 0) {
        data.forEach((wo, index) => {
            const statusText = getStatusText(wo.status);
            const statusClass = getStatusClass(wo.status);
            
            html += `
                <div class="work-order-section mb-4">
                    <div class="card border-0 shadow-sm">
                        <div class="card-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px 8px 0 0;">
                            <h6 class="mb-0">
                                <i class="fa fa-cogs mr-2"></i>İş Emri: ${wo.name}
                            </h6>
                        </div>
                        <div class="card-body p-0">
                            <div class="table-responsive">
                                <table class="table table-sm table-hover mb-0">
                                    <thead style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white;">
                                        <tr>
                                            <th style="border: none;">İş Emri</th>
                                            <th style="border: none;">Durum</th>
                                            <th style="border: none;">Miktar</th>
                                            <th style="border: none;">Üretilen</th>
                                            <th style="border: none;">Planlanan Başlangıç</th>
                                            <th style="border: none;">Planlanan Bitiş</th>
                                            <th style="border: none;">Fiili Başlangıç</th>
                                            <th style="border: none;">Fiili Bitiş</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>
                                                <a href="/app/work-order/${wo.name}" target="_blank" class="font-weight-bold text-primary">
                                                    ${wo.name}
                                                </a>
                                            </td>
                                            <td>
                                                <span class="badge badge-${statusClass}" style="font-size: 0.8rem;">${statusText}</span>
                                            </td>
                                            <td>
                                                <span class="badge badge-info" style="font-size: 0.8rem;">${wo.qty || 0}</span>
                                            </td>
                                            <td>
                                                <span class="badge badge-success" style="font-size: 0.8rem;">${wo.produced_qty || 0}</span>
                                            </td>
                                            <td>
                                                <span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(wo.planned_start_date)}</span>
                                            </td>
                                            <td>
                                                <span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(wo.planned_end_date)}</span>
                                            </td>
                                            <td>
                                                <span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(wo.actual_start_date)}</span>
                                            </td>
                                            <td>
                                                <span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(wo.actual_end_date)}</span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="operations-section mt-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="text-info mb-0">
                                <i class="fa fa-list mr-2"></i>Operasyonlar:
                            </h6>
                            <button class="btn btn-sm btn-outline-info" onclick="toggleOperations('${wo.name}')" id="toggle-btn-${wo.name}">
                                <i class="fa fa-chevron-down" id="chevron-${wo.name}"></i> Göster
                            </button>
                        </div>
                        <div class="operations-container" id="operations-content-${wo.name}" style="display: none;">
                            <div class="text-center p-3">
                                <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
                                <span class="ml-2">Operasyonlar yükleniyor...</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            

        });
    } else {
        html = '<div class="alert alert-info text-center">İş emri bulunamadı</div>';
    }
    
    try {
        content.html(html);
        console.log('Work Orders Modal updated successfully');
    } catch (error) {
        console.error('Error updating Work Orders Modal:', error);
        content.html('<div class="alert alert-danger">Modal güncellenirken hata oluştu</div>');
    }
}

function showWorkOrderOperations(workOrderName) {
    const modalId = 'work-order-operations-' + Date.now();
    const cacheKey = `work-order-operations-${workOrderName}`;
    
    // Cache kontrolü
    const cachedData = modalCache.get(cacheKey);
    if (cachedData && (Date.now() - cachedData.timestamp) < MODAL_CACHE_DURATION) {
        const modal = createModal(modalId, `İş Emri: ${workOrderName} - Operasyon Detayları`, 'modal-xl');
        setTimeout(() => {
            updateWorkOrderOperationsModal(cachedData.data, workOrderName, modalId);
        }, 100);
        return;
    }
    
    const modal = createModal(modalId, `İş Emri: ${workOrderName} - Operasyon Detayları`, 'modal-xl');
    
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
    
    if (operationsContainer.is(':visible')) {
        // Operasyonları gizle
        operationsContainer.hide();
        chevron.removeClass('fa-chevron-up').addClass('fa-chevron-down');
        toggleBtn.html('<i class="fa fa-chevron-down" id="chevron-' + workOrderName + '"></i> Göster');
    } else {
        // Operasyonları göster
        operationsContainer.show();
        chevron.removeClass('fa-chevron-down').addClass('fa-chevron-up');
        toggleBtn.html('<i class="fa fa-chevron-up" id="chevron-' + workOrderName + '"></i> Gizle');
        
        // Eğer operasyonlar daha önce yüklenmemişse yükle
        if (operationsContainer.find('.operations-table').length === 0) {
            loadWorkOrderOperations(workOrderName, operationsContainer);
        }
    }
}

function loadWorkOrderOperations(workOrderName, container) {
    // API çağrısı
    frappe.call({
        method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_takip.uretim_planlama_takip.get_work_order_operations_for_takip',
        args: { work_order_name: workOrderName },
        timeout: 15,
        callback: function(r) {
            console.log('Operasyon API Response:', r);
            console.log('Operasyon API Message:', r.message);
            
            if (r.exc) {
                console.error('Operasyon API Error:', r.exc);
                container.html('<div class="alert alert-danger p-3">Operasyon detayları yüklenirken hata: ' + r.exc + '</div>');
                return;
            }
            
            const data = r.message;
            console.log('Operasyon Data:', data);
            
            if (!data) {
                console.error('Operasyon data is null/undefined');
                container.html('<div class="alert alert-danger p-3">Operasyon verisi alınamadı</div>');
                return;
            }
            
            if (data.error) {
                console.error('Operasyon data error:', data.error);
                container.html('<div class="alert alert-danger p-3">' + data.error + '</div>');
                return;
            }
            
            console.log('Operasyonlar başarıyla yüklendi:', data.operations);
            updateWorkOrderOperationsContent(data, container);
        },
        error: function(err) {
            container.html('<div class="alert alert-danger p-3">Bağlantı hatası: ' + err + '</div>');
        }
    });
}

function updateWorkOrderOperationsContent(data, container) {
    const operations = data.operations || [];
    
    let html = `
        <div class="operations-table">
            <div class="table-responsive">
                <table class="table table-sm table-hover mb-0">
                    <thead style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white;">
                        <tr>
                            <th style="border: none;">Operasyon</th>
                            <th style="border: none;">İş İstasyonu</th>
                            <th style="border: none;">Durum</th>
                            <th style="border: none;">Tamamlanan</th>
                            <th style="border: none;">Planlanan Başlangıç</th>
                            <th style="border: none;">Planlanan Bitiş</th>
                            <th style="border: none;">Fiili Başlangıç</th>
                            <th style="border: none;">Fiili Bitiş</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    if (operations && operations.length > 0) {
        operations.forEach((op, index) => {
            const statusText = getStatusText(op.status);
            const statusClass = getStatusClass(op.status);
            
            html += `
                <tr>
                    <td><strong class="text-primary">${op.operation || '-'}</strong></td>
                    <td><span class="badge badge-info" style="font-size: 0.8rem;">${op.workstation || '-'}</span></td>
                    <td><span class="badge badge-${statusClass}" style="font-size: 0.8rem;">${statusText}</span></td>
                    <td><span class="badge badge-success" style="font-size: 0.8rem;">${op.completed_qty || 0}</span></td>
                    <td><span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(op.planned_start_time)}</span></td>
                    <td><span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(op.planned_end_time)}</span></td>
                    <td><span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(op.actual_start_time)}</span></td>
                    <td><span class="badge badge-warning" style="font-size: 0.8rem;">${formatDate(op.actual_end_time)}</span></td>
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
    `;
    
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
                            <span class="badge badge-${getStatusClass(currentStatus)}">${statusOptions[currentStatus] || currentStatus}</span>
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
                        <span class="badge badge-${getStatusClass(workOrder.status)}">${getStatusText(workOrder.status)}</span>
                    </td>
                    <td>
                        <span class="badge badge-info">${workOrder.qty || 0}</span>
                    </td>
                    <td>
                        <span class="badge badge-success">${workOrder.produced_qty || 0}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${formatDate(workOrder.planned_start_date)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${formatDate(workOrder.planned_end_date)}</span>
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
                                <th>İş İstasyonu</th>
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
            const statusText = getStatusText(op.status);
            const statusClass = getStatusClass(op.status);
            
            html += `
                <tr>
                    <td>
                        <strong>${op.operation || '-'}</strong>
                    </td>
                    <td>
                        <span class="badge badge-info">${op.workstation || '-'}</span>
                    </td>
                    <td>
                        <span class="badge badge-${statusClass}">${statusText}</span>
                    </td>
                    <td>
                        <span class="badge badge-success">${op.completed_qty || 0}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${formatDate(op.planned_start_time)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${formatDate(op.planned_end_time)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${formatDate(op.actual_start_time)}</span>
                    </td>
                    <td>
                        <span class="badge badge-warning">${formatDate(op.actual_end_time)}</span>
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

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleDateString('tr-TR');
    } catch {
        return dateStr;
    }
} 

function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '-';
    try {
        const date = new Date(dateTimeStr);
        return date.toLocaleString('tr-TR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateTimeStr;
    }
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
                    <tr><td><strong>Durum:</strong></td><td>${getStatusBadge(data.status)}</td></tr>
                    <tr><td><strong>Planlanan Başlangıç:</strong></td><td>${formatDate(data.planned_start_date)}</td></tr>
                    <tr><td><strong>Planlanan Bitiş:</strong></td><td>${formatDate(data.planned_end_date)}</td></tr>
                    <tr><td><strong>Gerçek Başlangıç:</strong></td><td>${formatDate(data.actual_start_date)}</td></tr>
                    <tr><td><strong>Gerçek Bitiş:</strong></td><td>${formatDate(data.actual_end_date)}</td></tr>
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