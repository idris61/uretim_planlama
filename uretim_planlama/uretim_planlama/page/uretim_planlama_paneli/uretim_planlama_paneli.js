// Utility functions - Global scope'ta
const utils = {
	// Table sorting utilities
	tableSorting: {
		currentSort: {
			planned: { column: null, direction: 'asc' },
			unplanned: { column: null, direction: 'asc' }
		},
		
		sortTable: function(tableType, column, data) {
			const currentSort = this.currentSort[tableType];
			
			// Toggle direction if same column
			if (currentSort.column === column) {
				currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
			} else {
				currentSort.column = column;
				currentSort.direction = 'asc';
			}
			
			return this.sortData(data, column, currentSort.direction);
		},
		
		sortData: function(data, column, direction) {
			if (!data || !Array.isArray(data)) return data;
			
			return data.sort((a, b) => {
				let valueA = a[column];
				let valueB = b[column];
				
				// Handle dates
				if (column.includes('tarihi') || column.includes('date')) {
					valueA = valueA ? new Date(valueA) : new Date(0);
					valueB = valueB ? new Date(valueB) : new Date(0);
				}
				// Handle numbers
				else if (typeof valueA === 'string' && !isNaN(parseFloat(valueA))) {
					valueA = parseFloat(valueA) || 0;
					valueB = parseFloat(valueB) || 0;
				}
				// Handle strings
				else {
					valueA = (valueA || '').toString().toLowerCase();
					valueB = (valueB || '').toString().toLowerCase();
				}
				
				if (direction === 'desc') {
					return valueA < valueB ? 1 : valueA > valueB ? -1 : 0;
				} else {
					return valueA < valueB ? -1 : valueA > valueB ? 1 : 0;
				}
			});
		},
		
		updateSortIcons: function(tableType, column) {
			const tableId = tableType === 'planned' ? 'planned-table' : 'planlanmamis-table';
			const table = document.getElementById(tableId);
			if (!table) return;
			
			// Remove all sort icons
			table.querySelectorAll('.sort-icon').forEach(icon => icon.remove());
			
			// Add icon to current sorted column
			const currentSort = this.currentSort[tableType];
			if (currentSort.column === column) {
				const header = table.querySelector(`th[data-column="${column}"]`);
				if (header) {
					const icon = document.createElement('i');
					icon.className = `fa fa-sort-${currentSort.direction === 'asc' ? 'up' : 'down'} sort-icon ml-1`;
					icon.style.color = '#007bff';
					header.appendChild(icon);
				}
			}
		}
	},
    // Güvenli HTML escape - Performance optimized
    escapeHtml: (text) => {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Debounce function - Memory leak prevention
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
            if (!dateStr) return '-';
            
            // Check cache first
            if (cache.has(dateStr)) {
                return cache.get(dateStr);
            }
            
            try {
                const date = new Date(dateStr);
                if (isNaN(date.getTime())) return dateStr;
                const formatted = date.toLocaleDateString('tr-TR');
                cache.set(dateStr, formatted);
                return formatted;
            } catch (e) {
                return dateStr;
            }
        };
    })(),

    // Safe number formatting - Optimized
    formatNumber: (num, decimals = 1) => {
        if (num === null || num === undefined || num === '') return '0';
        const parsed = parseFloat(num);
        return isNaN(parsed) ? '0' : parsed.toFixed(decimals);
    },

    // Modern status badge utility - Cached
    getStatusBadge: (() => {
        const statusMap = new Map([
            ['Completed', { label: 'Tamamlandı', bg: '#28a745', color: '#fff' }],
            ['In Process', { label: 'Devam Ediyor', bg: '#17a2b8', color: '#fff' }],
            ['Not Started', { label: 'Başlamadı', bg: '#6c757d', color: '#fff' }],
            ['Stopped', { label: 'Durduruldu', bg: '#dc3545', color: '#fff' }],
            ['Closed', { label: 'Kapatıldı', bg: '#6c757d', color: '#fff' }]
        ]);
        
        return (status) => {
            const statusInfo = statusMap.get(status) || { label: status, bg: '#6c757d', color: '#fff' };
            return `<span class="badge" style="background-color: ${statusInfo.bg}; color: ${statusInfo.color}; font-size: 0.75rem; padding: 3px 5px; border-radius: 4px;">${statusInfo.label}</span>`;
        };
    })(),

    // Row class utility for modern coloring - Optimized
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
            
            // Check cache
            if (cache.has(deliveryDate)) {
                return cache.get(deliveryDate);
            }
            
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

    // Text truncation utility - Performance optimized
    truncateText: (text, maxLength = 20, suffix = '...') => {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength - suffix.length) + suffix;
    },

    // DOM element creation utility - Performance optimized
    createElement: (tag, className = '', innerHTML = '') => {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    },

    // Event delegation utility - Performance optimized
    delegate: (container, selector, event, handler) => {
        container.addEventListener(event, (e) => {
            const target = e.target.closest(selector);
            if (target && container.contains(target)) {
                handler.call(target, e, target);
            }
        });
    },

    // Teslim tarihi hesaplama
    getDeliveryDate: (endDate, startDate) => {
        // Önce planned_end_date'i kontrol et
        if (endDate) {
            try {
                const date = new Date(endDate);
                if (!isNaN(date.getTime())) {
                    return date.toLocaleDateString('tr-TR');
                }
            } catch (e) {
                console.warn('planned_end_date parse hatası:', e);
            }
        }
        
        // planned_end_date yoksa veya geçersizse, başlangıç tarihinden hesapla
        if (startDate) {
            try {
                const start = new Date(startDate);
                if (!isNaN(start.getTime())) {
                    let deliveryDate = new Date(start);
                    let workDaysAdded = 0;
                    
                    // 4 iş günü ekle (hafta sonları hariç)
                    while (workDaysAdded < 4) {
                        deliveryDate.setDate(deliveryDate.getDate() + 1);
                        
                        // Hafta sonu değilse iş günü say
                        const dayOfWeek = deliveryDate.getDay();
                        if (dayOfWeek !== 0 && dayOfWeek !== 6) { // 0 = Pazar, 6 = Cumartesi
                            workDaysAdded++;
                        }
                    }
                    
                    return deliveryDate.toLocaleDateString('tr-TR');
                }
            } catch (e) {
                console.warn('startDate parse hatası:', e);
            }
        }
        
        return '-';
    }
};

// Error handling
const errorHandler = {
    show: (message, title = 'Hata', type = 'error') => {
        try {
            if (frappe && frappe.msgprint) {
                frappe.msgprint({
                    title: title,
                    message: message,
                    indicator: type === 'error' ? 'red' : 'yellow'
                });
            } else {
                console.error(`${title}: ${message}`);
                // Fallback to alert only if frappe not available
                if (typeof alert !== 'undefined') {
                    alert(`${title}: ${message}`);
                }
            }
        } catch (error) {
            console.error('Error showing message:', error);
        }
    },

    log: (error, context = '') => {
        console.error(`[${context}] Error:`, error);
    },

    // Performance monitoring
    measureTime: (name, fn) => {
        const start = performance.now();
        const result = fn();
        const end = performance.now();
        return result;
    }
};

// API Service - Enhanced with retry logic and better error handling
const apiService = {
    async call(method, args = {}, retries = 3) {
        const attempt = async (attemptNumber) => {
            try {
                return new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(new Error('Request timeout'));
                    }, 10000);

                    frappe.call({
                        method: method,
                        args: args,
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
            const data = await this.call('uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_production_planning_data', {
                filters: JSON.stringify(filters)
            });
            
            if (!data) throw new Error('Boş veri döndü');
            
            return {
                planned: Array.isArray(data) ? data : (data.planned || []),
                unplanned: data.unplanned || []
            };
        } catch (error) {
            errorHandler.log(error, 'API');
            throw error;
        }
    }
};

// UI Components - Enhanced with performance optimizations
const uiComponents = {
    // Loading state management - Kaldırıldı
    setLoading: (isLoading) => {
        // setLoading fonksiyonu kaldırıldı - kontroller alanı artık yok
        console.log('setLoading kaldırıldı - loading state yönetilmeyecek');
    },

    // Update summary cards - Kaldırıldı
    updateSummary: (data) => {
        // updateSummary fonksiyonu kaldırıldı - özet kartlar artık kullanılmıyor
        console.log('uiComponents.updateSummary kaldırıldı');
    },

    // Render table rows - Enhanced with virtual scrolling support
    renderTableRows: (tbodyId, rows) => {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return;
        
        if (!rows || rows.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="13" class="text-center text-muted">
                    <i class="fa fa-info-circle mr-2"></i>Henüz planlama bulunmuyor
                </td></tr>
            `;
            return;
        }
        
        // Use DocumentFragment for better performance
        const fragment = document.createDocumentFragment();
        
        // Process rows in chunks for better performance
        const chunkSize = 50;
        const processChunk = (startIndex) => {
            const endIndex = Math.min(startIndex + chunkSize, rows.length);
            
            for (let i = startIndex; i < endIndex; i++) {
                const rowHtml = tbodyId === 'planlanan-tbody' 
                    ? this.createPlannedRow(rows[i])
                    : this.createUnplannedRow(rows[i]);
                
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = rowHtml;
                fragment.appendChild(tempDiv.firstElementChild);
            }
            
            if (endIndex < rows.length) {
                // Process next chunk asynchronously
                requestAnimationFrame(() => processChunk(endIndex));
            } else {
                // All chunks processed, update DOM
                tbody.innerHTML = '';
                tbody.appendChild(fragment);
            }
        };
        
        processChunk(0);
    },

    // Create planned row with modern styling - Optimized
    createPlannedRow: (item) => {
        const pvcCount = parseInt(item.pvc_count || 0);
        const camCount = parseInt(item.cam_count || 0);
        const isCompleted = item.plan_status === 'Completed';
        const rowClass = utils.getRowClass(pvcCount, camCount, isCompleted);
        const isUrgent = utils.isUrgentDelivery(item.bitis_tarihi);
        const urgentClass = isUrgent ? 'urgent-delivery' : '';
        
        // Optimize text truncation
        const musteriText = utils.truncateText(item.musteri || '-', 25);
        const siparisText = utils.truncateText(item.sales_order || '-', 20);
        const bayiText = utils.truncateText(item.bayi || '-', 15);

        return `
            <tr class="${rowClass} ${urgentClass} cursor-pointer" data-id="${utils.escapeHtml(item.opti_no || '')}" data-opti="${utils.escapeHtml(item.opti_no || '')}">
                <td class="text-center">
                    <span class="badge badge-info">${utils.escapeHtml(item.hafta || '-')}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-primary">${utils.escapeHtml(item.opti_no || '-')}</span>
                </td>
                <td title="${item.sales_order || '-'}">
                    <span class="font-weight-bold text-primary">${siparisText}</span>
                </td>
                <td title="${item.bayi || '-'}">${bayiText}</td>
                <td title="${item.musteri || '-'}">${musteriText}</td>
                <td class="text-center">
                    <span class="badge badge-warning">${utils.formatDate(item.siparis_tarihi)}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-danger">${utils.formatDate(item.bitis_tarihi)}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-danger">${pvcCount}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-primary">${camCount}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-success">${utils.formatNumber(item.toplam_mtul_m2)}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-warning">${utils.formatDate(item.planlanan_baslangic_tarihi)}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-info">${utils.escapeHtml(item.seri || '-')}</span>
                </td>
                <td class="text-center">
                    <span class="badge badge-warning">${utils.escapeHtml(item.renk || '-')}</span>
                </td>
            </tr>
        `;
    },

    // Create unplanned row - Optimized
    createUnplannedRow: (item) => {
        const statusBadge = utils.getSalesOrderStatusBadge ? utils.getSalesOrderStatusBadge(item) : { label: 'Bilinmiyor', bg: '#6c757d', color: '#fff' };
        const mlyBadge = item.mly_dosyasi_var ? 
            '<span class="badge badge-success">MLY</span>' : 
            '<span class="badge badge-secondary">YOK</span>';
        const kismiPlanlamaBadge = item.kismi_planlama ? 
            '<span class="badge badge-warning">KISMİ</span>' : 
            '<span class="badge badge-info">TAM</span>';
        const isUrgent = item.acil == 1;
        const urgentBadge = isUrgent ? 
            '<span class="badge badge-danger">ACİL</span>' : 
            '<span class="badge badge-success">NORMAL</span>';

        return `
            <tr class="cursor-pointer" data-id="${utils.escapeHtml(item.sales_order || '')}">
                <td>${utils.escapeHtml(item.sales_order || '-')}</td>
                <td><strong>${utils.escapeHtml(item.bayi || '-')}</strong></td>
                <td><strong>${utils.escapeHtml(item.musteri || '-')}</strong></td>
                <td>${utils.formatDate(item.siparis_tarihi)}</td>
                <td>${utils.formatDate(item.bitis_tarihi)}</td>
                <td><span class="badge" style="background-color: ${statusBadge.bg}; color: ${statusBadge.color};">${statusBadge.label}</span></td>
                <td>${mlyBadge}</td>
                <td>${kismiPlanlamaBadge}</td>
                <td><span class="badge badge-danger">${utils.escapeHtml(item.pvc_count || '0')}</span></td>
                <td><span class="badge badge-primary">${utils.escapeHtml(item.cam_count || '0')}</span></td>
                <td><span class="badge badge-info">${utils.escapeHtml(item.seri || '-')}</span></td>
                <td><span class="badge badge-warning">${utils.escapeHtml(item.renk || '-')}</span></td>
                <td>${utils.escapeHtml(item.aciklama || '-')}</td>
                <td>${urgentBadge}</td>
            </tr>
        `;
    }
};

// Status badge utilities - Modern ve gelişmiş
const statusUtils = {
    getStatusBadge: (status) => {
        const statusMap = {
            'Draft': { label: 'Taslak', bg: '#6c757d', color: '#fff' },
            'Not Started': { label: 'Başlamadı', bg: '#ffc107', color: '#000' },
            'In Process': { label: 'İşlemde', bg: '#17a2b8', color: '#fff' },
            'Completed': { label: 'Tamamlandı', bg: '#28a745', color: '#fff' },
            'Stopped': { label: 'Durduruldu', bg: '#dc3545', color: '#fff' },
            'Closed': { label: 'Kapatıldı', bg: '#6c757d', color: '#fff' },
            'Pending': { label: 'Beklemede', bg: '#fd7e14', color: '#fff' },
            'Work In Progress': { label: 'İşlemde', bg: '#17a2b8', color: '#fff' },
            'Material Transferred': { label: 'Malzeme Transfer', bg: '#20c997', color: '#fff' },
            'Over Time': { label: 'Fazla Süre', bg: '#e83e8c', color: '#fff' }
        };
        
        return statusMap[status] || { label: status, bg: '#6c757d', color: '#fff' };
    },
    
    createStatusBadge: (statusBadgeData) => {
        if (!statusBadgeData || !statusBadgeData.class) {
            return `<span class="badge badge-secondary">-</span>`;
        }
        
        return `<span class="badge badge-${statusBadgeData.class}">${utils.escapeHtml(statusBadgeData.label)}</span>`;
    },
    
    createProgressBar: (percentage, size = 'sm') => {
        const percent = Math.min(100, Math.max(0, percentage || 0));
        const colorClass = percent >= 100 ? 'success' : percent >= 50 ? 'warning' : 'info';
        
        return `
            <div class="progress progress-${size}" style="height: 20px;">
                <div class="progress-bar bg-${colorClass}" role="progressbar" 
                     style="width: ${percent}%" aria-valuenow="${percent}" 
                     aria-valuemin="0" aria-valuemax="100">
                    ${percent.toFixed(1)}%
                </div>
            </div>
        `;
    },

    getSalesOrderStatusBadge: (item) => {
        const status = item.status || item.sales_order_status || 'Unknown';
        const statusMap = {
            'Draft': { label: 'Taslak', bg: '#6c757d', color: '#fff' },
            'To Deliver and Bill': { label: 'Teslim ve Fatura', bg: '#17a2b8', color: '#fff' },
            'To Bill': { label: 'Fatura', bg: '#28a745', color: '#fff' },
            'Completed': { label: 'Tamamlandı', bg: '#28a745', color: '#fff' },
            'Closed': { label: 'Kapatıldı', bg: '#6c757d', color: '#fff' },
            'Cancelled': { label: 'İptal', bg: '#dc3545', color: '#fff' },
            'Pending Approval': { label: 'Onay Bekliyor', bg: '#ffc107', color: '#000' },
            'Approved': { label: 'Onaylandı', bg: '#28a745', color: '#fff' },
            'Rejected': { label: 'Reddedildi', bg: '#dc3545', color: '#fff' },
            'Under Review': { label: 'İncelemede', bg: '#fd7e14', color: '#fff' },
            'Pending Finance': { label: 'Muhasebe Bekliyor', bg: '#17a2b8', color: '#fff' },
            'Finance Approved': { label: 'Muhasebe Onayı', bg: '#28a745', color: '#fff' },
            'Ready for Production': { label: 'Üretime Hazır', bg: '#20c997', color: '#fff' },
            'In Production': { label: 'Üretimde', bg: '#17a2b8', color: '#fff' }
        };
        
        return statusMap[status] || { label: status, bg: '#6c757d', color: '#fff' };
    }
};

// Status utilities'i utils'e ekle
utils.getStatusBadge = statusUtils.getStatusBadge;
utils.getSalesOrderStatusBadge = statusUtils.getSalesOrderStatusBadge;

// State management
const state = {
    // Current data
    plannedData: [],
    unplannedData: [],
    summaryData: {},
    
    // UI state
    isLoading: false,
    currentView: 'planned', // 'planned' or 'unplanned'
    currentFilters: {},
    
    // Pagination
    currentPage: 1,
    itemsPerPage: 50,
    
    // Search
    searchTerm: '',
    
    // Update methods
    setPlannedData: (data) => {
        state.plannedData = data || [];
    },
    
    setUnplannedData: (data) => {
        state.unplannedData = data || [];
    },
    
    setSummaryData: (data) => {
        state.summaryData = data || {};
    },
    
    setLoading: (loading) => {
        state.isLoading = loading;
    },
    
    setCurrentView: (view) => {
        state.currentView = view;
    },
    
    setFilters: (filters) => {
        state.currentFilters = { ...filters };
    },
    
    setSearchTerm: (term) => {
        state.searchTerm = term;
    },
    
    // Get current data based on view
    getCurrentData: () => {
        return state.currentView === 'planned' ? state.plannedData : state.unplannedData;
    },
    
    // Get filtered data
    getFilteredData: () => {
        let data = state.getCurrentData();
        
        // Apply search filter
        if (state.searchTerm) {
            const term = state.searchTerm.toLowerCase();
            data = data.filter(item => {
                return (
                    (item.opti_no && item.opti_no.toLowerCase().includes(term)) ||
                    (item.sales_order && item.sales_order.toLowerCase().includes(term)) ||
                    (item.bayi && item.bayi.toLowerCase().includes(term)) ||
                    (item.musteri && item.musteri.toLowerCase().includes(term)) ||
                    (item.seri && item.seri.toLowerCase().includes(term)) ||
                    (item.renk && item.renk.toLowerCase().includes(term))
                );
            });
        }
        
        // Apply other filters
        if (state.currentFilters.hafta) {
            data = data.filter(item => item.hafta === state.currentFilters.hafta);
        }
        
        if (state.currentFilters.seri) {
            data = data.filter(item => item.seri === state.currentFilters.seri);
        }
        
        if (state.currentFilters.renk) {
            data = data.filter(item => item.renk === state.currentFilters.renk);
        }
        
        return data;
    }
};

// Modal yönetimi fonksiyonları - Enhanced
const modalManager = {
    activeModals: new Set(),
    modalCache: new Map(),
    CACHE_DURATION: 60000,

    closeAllModals() {
        // Tüm modal'ları hızlıca kapat ve DOM'dan kaldır
        $('.modal').each(function() {
            const modal = $(this);
            modal.modal('hide');
            // Modal tamamen kapandıktan sonra DOM'dan kaldır
            modal.on('hidden.bs.modal', function() {
                modal.remove();
            });
        });
        this.activeModals.clear();
    },

    closeOtherModals(currentModalId) {
        // Diğer modal'ları hızlıca kapat ve DOM'dan kaldır
        $('.modal').not(`#${currentModalId}`).each(function() {
            const otherModal = $(this);
            otherModal.modal('hide');
            // Modal tamamen kapandıktan sonra DOM'dan kaldır
            otherModal.on('hidden.bs.modal', function() {
                otherModal.remove();
                modalManager.activeModals.delete(otherModal.attr('id'));
            });
        });
    },

    createModal(modalId, title, size = 'modal-lg') {
        this.closeOtherModals(modalId);
        
        const modalHtml = `
            <div class="modal" id="${modalId}" tabindex="-1" data-backdrop="static" data-keyboard="false">
                <div class="modal-dialog ${size}">
                    <div class="modal-content" style="background: white; border: none;">
                        <div class="modal-header" style="background: #dc3545; color: white; border: none;">
                            <h5 class="modal-title">
                                <i class="fa fa-spinner fa-spin mr-2"></i>${title}
                            </h5>
                            <button type="button" class="close text-white" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body" style="max-height: 70vh; overflow-y: scroll; background: white; color: #333;">
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
                return null;
            }
            
            modal.on('hidden.bs.modal', function() {
                $(this).remove();
                modalManager.activeModals.delete(modalId);
            });
            
            this.activeModals.add(modalId);
            // Modal'ı hızlıca göster
            modal.modal({
                show: true,
                backdrop: 'static',
                keyboard: false
            });
            
            return modal;
        } catch (error) {
            errorHandler.log(error, 'modalManager.createModal');
            return null;
        }
    },

    clearCache() {
        this.modalCache.clear();
        this.activeModals.clear();
        this.closeAllModals();
    }
};

// Configuration
const CONFIG = {
    // API endpoints
    ENDPOINTS: {
        PLANNED_DATA: 'uretim_planlama.uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_uretim_planlama_data',
        UNPLANNED_DATA: 'uretim_planlama.api.get_unplanned_data',
        SUMMARY_DATA: 'uretim_planlama.api.get_summary_data',
        UPDATE_PLANNING: 'uretim_planlama.api.update_planning',
        DELETE_PLANNING: 'uretim_planlama.api.delete_planning'
    },
    
    // Performance settings
    CACHE_DURATION: 300000, // 5 dakika - cache süresi artırıldı
    DATA_LOAD_TIMEOUT: 120000, // 2 dakika - timeout artırıldı
    
    // Table configurations
    TABLES: {
        PLANNED: {
            id: 'planned-table',
            tbodyId: 'planned-tbody',
            columns: [
                { key: 'hafta', label: 'Hafta', width: '8%' },
                { key: 'opti_no', label: 'Opti No', width: '12%' },
                { key: 'sales_order', label: 'Sipariş No', width: '10%' },
                { key: 'bayi', label: 'Bayi', width: '12%' },
                { key: 'musteri', label: 'Müşteri', width: '12%' },
                { key: 'siparis_tarihi', label: 'Sipariş Tarihi', width: '10%' },
                { key: 'bitis_tarihi', label: 'Bitiş Tarihi', width: '10%' },
                { key: 'pvc_count', label: 'PVC', width: '6%' },
                { key: 'cam_count', label: 'Cam', width: '6%' },
                { key: 'toplam_mtul_m2', label: 'Toplam m²', width: '8%' },
                { key: 'planlanan_baslangic_tarihi', label: 'Planlanan Başlangıç', width: '12%' },
                { key: 'seri', label: 'Seri', width: '6%' },
                { key: 'renk', label: 'Renk', width: '6%' }
            ]
        },
        UNPLANNED: {
            id: 'unplanned-table',
            tbodyId: 'unplanned-tbody',
            columns: [
                { key: 'sales_order', label: 'Sipariş No', width: '10%' },
                { key: 'bayi', label: 'Bayi', width: '12%' },
                { key: 'musteri', label: 'Müşteri', width: '12%' },
                { key: 'siparis_tarihi', label: 'Sipariş Tarihi', width: '10%' },
                { key: 'bitis_tarihi', label: 'Bitiş Tarihi', width: '10%' },
                { key: 'siparis_durumu', label: 'Durum', width: '8%' },
                { key: 'mly_dosyasi_var', label: 'MLY', width: '6%' },
                { key: 'kismi_planlama', label: 'Planlama', width: '8%' },
                { key: 'pvc_count', label: 'PVC', width: '6%' },
                { key: 'cam_count', label: 'Cam', width: '6%' },
                { key: 'seri', label: 'Seri', width: '6%' },
                { key: 'renk', label: 'Renk', width: '6%' },
                { key: 'aciklama', label: 'Açıklama', width: '8%' },
                { key: 'acil', label: 'Öncelik', width: '6%' }
            ]
        }
    },
    
    // Default filters
    DEFAULT_FILTERS: {
        hafta: '',
        seri: '',
        renk: '',
        start_date: '',
        end_date: ''
    },
    
    // Pagination - Tüm verileri göster
    PAGINATION: {
        DEFAULT_PAGE_SIZE: 0, // 0 = tüm veriler
        PAGE_SIZE_OPTIONS: [0, 100, 500, 1000] // 0 = sınırsız
    },
    
    // Refresh intervals (in milliseconds)
    REFRESH_INTERVALS: {
        AUTO_REFRESH: 30000, // 30 seconds
        MANUAL_REFRESH: 5000  // 5 seconds
    }
};

frappe.pages['uretim_planlama_paneli'] = frappe.pages['uretim_planlama_paneli'] || {};

class UretimPlanlamaPaneli {
	constructor(page) {
		this.page = page;
		this.initialized = false;
		this.refreshTimer = null;
		this.debouncedRefresh = utils.debounce(this.loadProductionData.bind(this), 500);
		this.eventListeners = new Map();
		this.observers = new Map();
		
		// Performance optimization cache
		this.dataCache = new Map();
		this.lastCacheUpdate = 0;
		this.lastUpdate = 0;
		this.updateInterval = null;
		this.debounceTimer = null;
		
		// Independent table states
		this.plannedTable = {
			data: [],
			filters: {},
			isLoading: false,
			showCompleted: false
		};
		
		this.unplannedTable = {
			data: [],
			filters: {},
			isLoading: false
		};
		
		// Enhanced error handling
		this.errorContext = 'UretimPlanlamaPaneli';
		
		this.init();
	}

	async init() {
		try {
			this.addCustomStyles();
			this.ensureSidebarOpen();
			this.createPage();
			this.initControls();
			this.initSummary();
			this.initTables();
			this.initCuttingTable();
			this.bindEvents();
			
			// Load initial data for both tables independently
			await Promise.all([
				this.loadPlannedData(),
				this.loadUnplannedData()
			]);
			
			// Overview summary'yi yükle
			this.loadOverviewSummaryData();
			
			this.startAutoRefresh();
			this.initialized = true;
			
		} catch (error) {
			console.error('UretimPlanlamaPaneli.init Error:', error);
			frappe.msgprint('Sayfa başlatılırken hata oluştu: ' + error.message);
		}
	}

	ensureSidebarOpen() {
		// Sidebar'ı basit şekilde aç
		setTimeout(() => {
			// ERPNext'in sidebar toggle'ını çağır
			if (typeof frappe !== 'undefined' && frappe.ui && frappe.ui.toolbar) {
				try {
					// Eğer sidebar kapalıysa aç
					if ($('body').hasClass('sidebar-collapsed')) {
						$('.navbar-toggle-sidebar').click();
					}
					
					// Local storage'da açık durumu kaydet
					localStorage.setItem('sidebar_collapsed', '0');
				} catch (e) {
					console.log('Sidebar toggle hatası:', e);
				}
			}
		}, 500);
	}

	createPage() {
		this.page.main.html(`
			<div class="container-fluid" style="max-width: 100%; padding: 0;">
				<!-- Profil Stok Paneli Butonu - Üst sağ köşede -->
				<div class="row mb-3">
					<div class="col-12 text-right">
						<button class="btn btn-success" id="profil-stok-paneli-btn" style="font-size: 1rem; padding: 10px 24px; border-radius: 25px; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);">
							<i class="fa fa-cubes mr-2"></i>
							Profil Stok Paneli
						</button>
					</div>
				</div>
				
				<!-- PVC-CAM Overview Header -->
				<div class="row mb-3">
					<div class="col-12">
						<h4 class="mb-0" style="color: #333; font-weight: 700;">
							<i class="fa fa-chart-pie mr-2"></i>
							Üretim Durumu Özeti
						</h4>
					</div>
				</div>
				
				<div class="row no-gutters">
							<!-- PVC BÖLÜMÜ -->
							<div class="col-md-6" style="background: #fff3cd; border: 3px solid #ffc107; border-right: 1.5px solid #ffc107;">
								<div class="text-center py-2" style="background: #ffc107; color: #000; font-weight: 700; font-size: 1.1rem;">
									<i class="fa fa-cube mr-2"></i>PVC
								</div>

								<div class="table-responsive">
									<table class="table table-sm mb-0" style="font-size: 0.9rem;">
										<tbody id="overview-pvc-tbody" style="background: #fff8dc;">
											<tr style="background: #fff3cd;">
												<td style="padding: 15px; text-align: center; font-size: 2rem; font-weight: 800; color: #856404; border: 2px solid #ffc107; background: #fff3cd;">
													<div style="font-size: 1.2rem; color: #000;">ADET</div>
													<div id="pvc-adet" style="font-size: 2.5rem; font-weight: 900;">739</div>
												</td>
												<td style="padding: 15px; text-align: center; font-size: 2rem; font-weight: 800; color: #856404; border: 2px solid #ffc107; background: #fff3cd;">
													<div style="font-size: 1.2rem; color: #000;">MTÜL</div>
													<div id="pvc-mtul" style="font-size: 2.5rem; font-weight: 900;">9923</div>
												</td>
											</tr>
											<tr style="background: #fff8dc;">
												<td style="padding: 12px; text-align: center; color: #000; border: 1px solid #ffc107;">
													<div style="font-size: 0.9rem; font-weight: 600;">GÜNLÜK ORTALAMA ÜRETİM</div>
													<div id="pvc-gunluk" style="font-size: 1.5rem; font-weight: 800; color: #856404;">120</div>
												</td>
												<td style="padding: 12px; text-align: center; color: #000; border: 1px solid #ffc107;">
													<div style="font-size: 0.9rem; font-weight: 600;">PVC ÜRETİM GÜN SAYISI</div>
													<div id="pvc-gun-sayisi" style="font-size: 1.5rem; font-weight: 800; color: #856404;">6,2</div>
												</td>
											</tr>
											<tr style="background: #fff3cd;">
												<td colspan="2" style="padding: 12px; text-align: center; color: #000; border: 2px solid #ffc107;">
													<div style="font-size: 0.9rem; font-weight: 600;">TAHMİNİ BİTİŞ TARİHİ</div>
													<div id="pvc-bitis-tarihi" style="font-size: 1.3rem; font-weight: 800; color: #856404;">21.08.2025</div>
												</td>
											</tr>
										</tbody>
									</table>
								</div>
							</div>
							
							<!-- CAM BÖLÜMÜ -->
							<div class="col-md-6" style="background: #d1ecf1; border: 3px solid #17a2b8; border-left: 1.5px solid #17a2b8;">
								<div class="text-center py-2" style="background: #17a2b8; color: white; font-weight: 700; font-size: 1.1rem;">
									<i class="fa fa-square mr-2"></i>CAM
								</div>

								<div class="table-responsive">
									<table class="table table-sm mb-0" style="font-size: 0.9rem;">
										<tbody id="overview-cam-tbody" style="background: #d1ecf1;">
											<tr style="background: #bee5eb;">
												<td style="padding: 15px; text-align: center; font-size: 2rem; font-weight: 800; color: #0c5460; border: 2px solid #17a2b8; background: #bee5eb;">
													<div style="font-size: 1.2rem; color: #000;">ADET</div>
													<div id="cam-adet" style="font-size: 2.5rem; font-weight: 900;">316</div>
												</td>
												<td style="padding: 15px; text-align: center; font-size: 2rem; font-weight: 800; color: #0c5460; border: 2px solid #17a2b8; background: #bee5eb;">
													<div style="font-size: 1.2rem; color: #000;">M2</div>
													<div id="cam-m2" style="font-size: 2.5rem; font-weight: 900;">302</div>
												</td>
											</tr>
											<tr style="background: #d1ecf1;">
												<td style="padding: 12px; text-align: center; color: #000; border: 1px solid #17a2b8;">
													<div style="font-size: 0.9rem; font-weight: 600;">GÜNLÜK ORTALAMA ÜRETİM</div>
													<div id="cam-gunluk" style="font-size: 1.5rem; font-weight: 800; color: #0c5460;">350</div>
												</td>
												<td style="padding: 12px; text-align: center; color: #000; border: 1px solid #17a2b8;">
													<div style="font-size: 0.9rem; font-weight: 600;">CAM ÜRETİM GÜN SAYISI</div>
													<div id="cam-gun-sayisi" style="font-size: 1.5rem; font-weight: 800; color: #0c5460;">0,9</div>
												</td>
											</tr>
											<tr style="background: #bee5eb;">
												<td colspan="2" style="padding: 12px; text-align: center; color: #000; border: 2px solid #17a2b8;">
													<div style="font-size: 0.9rem; font-weight: 600;">TAHMİNİ BİTİŞ TARİHİ</div>
													<div id="cam-bitis-tarihi" style="font-size: 1.3rem; font-weight: 800; color: #0c5460;">15.08.2025</div>
												</td>
											</tr>
										</tbody>
									</table>
								</div>
							</div>
				</div>
				

				
				<!-- Ana içerik buraya eklenecek -->
			</div>
		`);
	}

	addCustomStyles() {
		if (document.getElementById('uretim-planlama-paneli-styles')) return;
		
		const styles = `
			/* Ana Container Tam Genişlik */
			.container-fluid {
				max-width: 100% !important;
				padding: 0 5px !important;
				margin: 0 !important;
			}
			
			.row {
				margin: 0 !important;
			}
			
			.col-12, .col-md-4, .col-md-6 {
				padding: 0 5px !important;
			}
			
			/* Card'ları tam genişlik */
			.card {
				width: 100% !important;
				margin-bottom: 10px !important;
			}
			
					/* Modern Renk Kodlaması - ZORLA */
		.table-container .pvc-row, 
		tbody .pvc-row,
		tr.pvc-row { 
			background-color: #fff8dc !important; 
			border-left: 4px solid #ffc107 !important; 
		}
		
		.table-container .cam-row,
		tbody .cam-row, 
		tr.cam-row { 
			background-color: #e3f2fd !important; 
			border-left: 4px solid #17a2b8 !important; 
		}
		
		.table-container .mixed-row,
		tbody .mixed-row,
		tr.mixed-row { 
			background-color: #f8d7da !important; 
			border-left: 4px solid #dc3545 !important; 
		}
		
		.table-container .completed-row,
		tbody .completed-row,
		tr.completed-row { 
			background-color: #28a745 !important; 
			border-left: 4px solid #1e7e34 !important; 
			color: #ffffff !important; 
			font-weight: bold !important;
		}
		
		.table-container .default-row,
		tbody .default-row,
		tr.default-row { 
			background-color: #f8f9fa !important; 
			border-left: 4px solid #6c757d !important; 
		}
		
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

			.table-container::-webkit-scrollbar {
				width: 12px;
				height: 12px;
			}

			.table-container::-webkit-scrollbar-track {
				background: #f1f1f1;
				border-radius: 6px;
			}

			.table-container::-webkit-scrollbar-thumb {
				background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
				border-radius: 6px;
				border: 2px solid #f1f1f1;
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
				font-size: 0.75rem; 
				padding: 6px 2px; 
				text-align: center; 
				box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
				white-space: nowrap; 
				height: 32px; 
			}
			
			/* Kolon genişlikleri - Planlanan tablo için */
			#planlanan-tbody .table-container th:nth-child(1) { width: 5%; }    /* HAFTA */
			#planlanan-tbody .table-container th:nth-child(2) { width: 7%; }    /* OPTI NO */
			#planlanan-tbody .table-container th:nth-child(3) { width: 15%; }   /* SIPARIS NO */
			#planlanan-tbody .table-container th:nth-child(4) { width: 12%; }   /* BAYI */
			#planlanan-tbody .table-container th:nth-child(5) { width: 15%; }   /* MÜSTERI */
			#planlanan-tbody .table-container th:nth-child(6) { width: 8%; }    /* SIPARIŞ TARIHI */
			#planlanan-tbody .table-container th:nth-child(7) { width: 8%; }    /* TESLIM TARIHI */
			#planlanan-tbody .table-container th:nth-child(8) { width: 5%; }    /* PVC */
			#planlanan-tbody .table-container th:nth-child(9) { width: 5%; }    /* CAM */
			#planlanan-tbody .table-container th:nth-child(10) { width: 7%; }   /* MTUL/M² */
			#planlanan-tbody .table-container th:nth-child(11) { width: 8%; }   /* BAŞLANGIÇ */
			#planlanan-tbody .table-container th:nth-child(12) { width: 8%; }   /* SERI */
			#planlanan-tbody .table-container th:nth-child(13) { width: 7%; }   /* RENK */
			
			/* Kolon genişlikleri - Planlanmamış tablo için */
			#planlanmamis-tbody .table-container th:nth-child(1) { width: 12%; }   /* SIPARIS NO */
			#planlanmamis-tbody .table-container th:nth-child(2) { width: 12%; }   /* BAYI */
			#planlanmamis-tbody .table-container th:nth-child(3) { width: 15%; }   /* MÜSTERI */
			#planlanmamis-tbody .table-container th:nth-child(4) { width: 8%; }    /* SIPARIŞ TARIHI */
			#planlanmamis-tbody .table-container th:nth-child(5) { width: 8%; }    /* TESLIM TARIHI */
			#planlanmamis-tbody .table-container th:nth-child(6) { width: 10%; }   /* DURUM */
			#planlanmamis-tbody .table-container th:nth-child(7) { width: 5%; }    /* PVC */
			#planlanmamis-tbody .table-container th:nth-child(8) { width: 5%; }    /* CAM */
			#planlanmamis-tbody .table-container th:nth-child(9) { width: 7%; }    /* MTUL/M² */
			#planlanmamis-tbody .table-container th:nth-child(10) { width: 8%; }   /* SERI */
			#planlanmamis-tbody .table-container th:nth-child(11) { width: 7%; }   /* RENK */
			#planlanmamis-tbody .table-container th:nth-child(12) { width: 18%; }  /* AÇIKLAMA */
			#planlanmamis-tbody .table-container th:nth-child(13) { width: 5%; }   /* ACİL */

			.table-container tbody tr { 
				transition: all 0.3s ease; 
				height: 4rem !important; 
				border-bottom: 1px solid #dee2e6 !important; 
			}

			/* Genel hover efektini kaldır ve sadece sınıf bazlı hover'ları uygula */
			.table-container tbody tr:hover {
				/* Genel hover efektini iptal et */
				background: inherit !important;
				transform: none !important;
				box-shadow: none !important;
			}

			/* Sınıf bazlı hover efektleri - bu öncelikli */




			.table-container tbody td { 
				padding: 4px 2px !important; 
				font-size: 0.8rem !important; 
				font-weight: bold !important; 
				vertical-align: middle !important; 
				word-wrap: break-word !important;
				overflow: hidden !important;
				text-overflow: ellipsis !important;
			}

			/* Modern Card Stilleri */
			.card { 
				border: none; 
				box-shadow: 0 12px 35px rgba(0, 0, 0, 0.1); 
				border-radius: 16px; 
				margin-bottom: 2rem; 
			}

			/* Modern Button Stilleri */
			.btn { 
				border-radius: 10px; 
				padding: 12px 24px; 
				font-weight: 600; 
				transition: all 0.3s ease; 
				box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
			}

			.btn-primary { 
				background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
				border: none; 
			}

			/* Modern Form Stilleri */
			.form-control { 
				border-radius: 10px; 
				border: 2px solid #e9ecef; 
				padding: 12px 16px; 
				transition: all 0.3s ease; 
			}

			/* Filtre Stilleri */
			.filter-section {
				background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
				border-radius: 16px;
				padding: 8px 12px;
				margin-bottom: 15px;
				box-shadow: 0 8px 25px rgba(0,0,0,0.1);
			}

			.filter-single-row {
				display: flex;
				align-items: center;
				gap: 4px;
				flex-wrap: nowrap;
				padding: 4px 0;
				width: 100%;
			}

			.filter-inputs {
				display: flex;
				align-items: center;
				gap: 4px;
				flex: 1;
				flex-wrap: nowrap;
				width: 100%;
			}

			.filter-input-item {
				flex: 1;
				min-width: 0;
			}

			.filter-input-item input,
			.filter-input-item select {
				border-radius: 6px;
				font-size: 0.75rem;
				border: 1px solid #ced4da;
				padding: 4px 8px;
				height: 32px;
				width: 100%;
			}

			/* Badge Stilleri */
			.badge { 
				font-weight: bold; 
				font-size: 0.75rem; 
				border-radius: 4px; 
				padding: 3px 5px; 
			}

			/* Basit sidebar ayarı */
			.navbar-toggle-sidebar {
				display: none !important;
			}
			
			/* Container ve row düzenlemesi */
			.container-fluid {
				width: 100% !important;
				max-width: 100% !important;
				padding: 0 !important;
				margin: 0 !important;
			}
			
			.row {
				margin: 0 !important;
				width: 100% !important;
			}
			
			.col-12, .col-md-4, .col-md-6 {
				padding: 5px !important;
				margin: 0 !important;
			}
			
			/* Responsive */
			@media (max-width: 768px) {
				.table-container { font-size: 12px; }
				
				/* Mobilde de sidebar açık kalsın */
				.layout-side-section {
					position: relative !important;
					transform: none !important;
				}
			}
		`;
		
		const styleElement = document.createElement('style');
		styleElement.id = 'uretim-planlama-paneli-styles';
		styleElement.textContent = styles;
		document.head.appendChild(styleElement);
	}

	initControls() {
		// initControls fonksiyonu kaldırıldı - kontroller alanı artık kullanılmıyor

	}

	initSummary() {
		// initSummary fonksiyonu kaldırıldı - özet kartlar artık kullanılmıyor

	}

	initTables() {
		// Planned productions table - Independent
		const plannedRow = $('<div class="row mb-4"></div>').appendTo(this.page.body);
		const plannedCol = $('<div class="col-12"></div>').appendTo(plannedRow);
		
		plannedCol.append(`
			<div class="card mb-4">
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
							<button class="btn btn-outline-light btn-sm mr-3" id="toggle-completed-btn" style="white-space: nowrap; font-size: 0.8rem;">
								<i class="fa fa-eye-slash mr-1"></i>
								Tamamlananları Göster (0)
							</button>
							<div class="badge badge-light" style="font-size: 1.1rem; padding: 8px 12px; border-radius: 20px;" id="planlanan-count">0</div>
						</div>
					</div>
				</div>
				
				<div class="card-body p-0">
					<!-- Planlanan Üretimler Filtreleri - Modern -->
					<div class="filter-section planlanan-filter">
						<div class="filter-single-row">
							<div class="filter-inputs">
								<div class="filter-input-item">
									<input id="planlanan-opti-filter" class="form-control" placeholder="Opti No...">
								</div>
								<div class="filter-input-item">
									<input id="planlanan-siparis-filter" class="form-control" placeholder="Sipariş No...">
								</div>
								<div class="filter-input-item">
									<input id="planlanan-bayi-filter" class="form-control" placeholder="Bayi...">
								</div>
								<div class="filter-input-item">
									<input id="planlanan-musteri-filter" class="form-control" placeholder="Müşteri...">
								</div>
								<div class="filter-input-item">
									<input id="planlanan-seri-filter" class="form-control" placeholder="Seri...">
								</div>
								<div class="filter-input-item">
									<input id="planlanan-renk-filter" class="form-control" placeholder="Renk...">
								</div>
								<div class="filter-input-item">
									<select id="planlanan-tip-filter" class="form-control">
										<option value="">Tümü</option>
										<option value="PVC">PVC</option>
										<option value="Cam">Cam</option>
										<option value="Karışık">Karışık</option>
									</select>
								</div>
								<div class="filter-input-item">
									<button class="btn btn-danger" id="planlanan-clear-btn">
										× TEMİZLE
									</button>
								</div>
							</div>
						</div>
					</div>
					
					<div class="table-container">
						<table class="table table-hover mb-0" style="font-size: 0.8rem;">
							<thead style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-size: 0.7rem;">
								<tr>
									<th style="padding: 4px 2px;" data-column="hafta">Hafta</th>
									<th style="padding: 4px 2px;" data-column="opti_no">Opti No</th>
									<th style="padding: 4px 2px;" data-column="sales_order">Sipariş No</th>
									<th style="padding: 4px 2px;" data-column="bayi">Bayi</th>
									<th style="padding: 4px 2px;" data-column="musteri">Müşteri</th>
									<th style="padding: 4px 2px;" data-column="siparis_tarihi" class="sortable-header">Sipariş Tarihi <i class="fa fa-sort text-white-50 ml-1"></i></th>
									<th style="padding: 4px 2px;" data-column="teslim_tarihi" class="sortable-header">Teslim Tarihi <i class="fa fa-sort text-white-50 ml-1"></i></th>
									<th style="padding: 4px 2px;" data-column="pvc_qty">PVC</th>
									<th style="padding: 4px 2px;" data-column="cam_qty">Cam</th>
									<th style="padding: 4px 2px;" data-column="total_mtul">MTUL/m²</th>
									<th style="padding: 4px 2px;" data-column="baslangic_tarihi" class="sortable-header">Başlangıç <i class="fa fa-sort text-white-50 ml-1"></i></th>
									<th style="padding: 4px 2px;" data-column="seri">Seri</th>
									<th style="padding: 4px 2px;" data-column="renk">Renk</th>
								</tr>
							</thead>
							<tbody id="planlanan-tbody" style="font-size: 0.8rem;">
								<tr><td colspan="13" class="text-center text-muted">Veri yükleniyor...</td></tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`);

		// Unplanned orders table - Independent
		const unplannedRow = $('<div class="row mb-4"></div>').appendTo(this.page.body);
		const unplannedCol = $('<div class="col-12"></div>').appendTo(unplannedRow);
		
		unplannedCol.append(`
			<div class="card mb-4">
				<div class="card-header" style="background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%); color: white;">
					<div class="d-flex justify-content-between align-items-center">
						<div class="d-flex align-items-center">
							<div class="mr-3">
								<i class="fa fa-clock-o" style="font-size: 1.5rem;"></i>
							</div>
							<div>
								<h5 class="mb-0" style="font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">PLANLANMAMIŞ SİPARİŞLER</h5>
							</div>
						</div>
						<div class="d-flex align-items-center">
							<div class="badge badge-light" style="font-size: 1.1rem; padding: 8px 12px; border-radius: 20px;" id="planlanmamis-count">0</div>
						</div>
					</div>
				</div>
				
				<div class="card-body p-0">
					<!-- Planlanmamış Siparişler Filtreleri - Modern -->
					<div class="filter-section planlanmamis-filter">
						<div class="filter-single-row">
							<div class="filter-inputs">
								<div class="filter-input-item">
									<input id="planlanmamis-siparis-filter" class="form-control" placeholder="Sipariş No...">
								</div>
								<div class="filter-input-item">
									<input id="planlanmamis-bayi-filter" class="form-control" placeholder="Bayi...">
								</div>
								<div class="filter-input-item">
									<input id="planlanmamis-musteri-filter" class="form-control" placeholder="Müşteri...">
								</div>
								<div class="filter-input-item">
									<input id="planlanmamis-seri-filter" class="form-control" placeholder="Seri...">
								</div>
								<div class="filter-input-item">
									<input id="planlanmamis-renk-filter" class="form-control" placeholder="Renk...">
								</div>

								<div class="filter-input-item">
									<select id="planlanmamis-acil-filter" class="form-control">
										<option value="">Acil Durum</option>
										<option value="ACİL">ACİL</option>
										<option value="NORMAL">NORMAL</option>
									</select>
								</div>
								<div class="filter-input-item">
									<select id="planlanmamis-tip-filter" class="form-control">
										<option value="">Tümü</option>
										<option value="PVC">PVC</option>
										<option value="Cam">Cam</option>
									</select>
								</div>
								<div class="filter-input-item">
									<button class="btn btn-danger" id="planlanmamis-clear-btn">
										<i class="fa fa-times"></i> TEMİZLE
									</button>
								</div>
							</div>
						</div>
					</div>
					
					<div class="table-container">
						<table class="table table-hover mb-0" style="font-size: 0.8rem;">
							<thead style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-size: 0.7rem;">
								<tr>
									<th style="padding: 6px 6px;" data-column="sales_order">Sipariş No</th>
									<th style="padding: 6px 6px;" data-column="bayi">Bayi</th>
									<th style="padding: 6px 6px;" data-column="musteri">Müşteri</th>
									<th style="padding: 6px 6px;" data-column="siparis_tarihi" class="sortable-header">Sipariş Tarihi <i class="fa fa-sort text-white-50 ml-1"></i></th>
									<th style="padding: 6px 6px;" data-column="bitis_tarihi" class="sortable-header">Teslim Tarihi <i class="fa fa-sort text-white-50 ml-1"></i></th>
									<th style="padding: 6px 6px;" data-column="siparis_durumu">Durum</th>
									<th style="padding: 6px 6px;" data-column="pvc_count">PVC</th>
									<th style="padding: 6px 6px;" data-column="cam_count">Cam</th>
									<th style="padding: 6px 6px;" data-column="total_mtul">MTÜL/m²</th>
									<th style="padding: 6px 6px;" data-column="seri">Seri</th>
									<th style="padding: 6px 6px;" data-column="renk">Renk</th>
									<th style="padding: 6px 6px; min-width: 200px;" data-column="aciklama">Açıklama</th>
									<th style="padding: 6px 6px;" data-column="acil">Acil</th>
								</tr>
							</thead>
							<tbody id="planlanmamis-tbody" style="font-size: 0.8rem;">
								<tr><td colspan="13" class="text-center text-muted">Veri yükleniyor...</td></tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		`);
	}

	// Kesim Planı Tablosu - Üretim planı hazırlarken kapasite kontrolü için
	initCuttingTable() {
		const cuttingRow = $('<div class="row mb-4"></div>').appendTo(this.page.body);
		const cuttingCol = $('<div class="col-12"></div>').appendTo(cuttingRow);
		
		cuttingCol.append(`
			<div class="card mb-4">
				<div class="card-header" style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); color: white;">
					<div class="d-flex justify-content-between align-items-center">
						<div class="d-flex align-items-center">
							<div class="mr-3">
								<i class="fa fa-cut" style="font-size: 1.5rem;"></i>
							</div>
							<div>
								<h5 class="mb-0" style="font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">GÜNLÜK KESİM İSTASYONU TABLOSU</h5>
							</div>
						</div>
						<div class="d-flex align-items-center">
							<div class="badge badge-light" style="font-size: 1.1rem; padding: 8px 12px; border-radius: 20px;" id="cutting-count">0</div>
						</div>
					</div>
				</div>
				
				<div class="card-body p-0">
					<!-- Kesim Planı Filtreleri -->
					<div class="filter-section cutting-filter">
						<div class="filter-single-row">
							<div class="filter-inputs">
								<div class="filter-input-item">
									<input id="cutting-from-date" class="form-control" type="date" placeholder="Başlangıç Tarihi...">
								</div>
								<div class="filter-input-item">
									<input id="cutting-to-date" class="form-control" type="date" placeholder="Bitiş Tarihi...">
								</div>
								<div class="filter-input-item">
									<select id="cutting-production-type" class="form-control">
										<option value="">Tümü</option>
										<option value="pvc">PVC</option>
										<option value="cam">Cam</option>
									</select>
								</div>
								<div class="filter-input-item">
									<button class="btn btn-danger" id="cutting-clear-btn">
										<i class="fa fa-times"></i> TEMİZLE
									</button>
								</div>
							</div>
						</div>
					</div>
					
					<div id="cutting-matrix-table" class="p-3" style="max-height: 400px; overflow-y: auto;">
						<div class="text-center text-muted">
							<i class="fa fa-info-circle mr-2"></i>Kesim planı verileri yükleniyor...
						</div>
					</div>
				</div>
			</div>
		`);

		// İş İstasyonu Doluluk Oranları Tablosu
		const utilizationRow = $('<div class="row mb-4"></div>').appendTo(this.page.body);
		const utilizationCol = $('<div class="col-12"></div>').appendTo(utilizationRow);
		
		utilizationCol.append(`
			<div class="card mb-4">
				<div class="card-header" style="background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%); color: white;">
					<div class="d-flex justify-content-between align-items-center">
													<div class="d-flex align-items-center">
								<div class="mr-3">
									<i class="fa fa-tasks" style="font-size: 1.5rem;"></i>
								</div>
								<div>
									<h5 class="mb-0" style="font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">OPERASYON DOLULUK ORANI</h5>
								</div>
							</div>
						<div class="d-flex align-items-center">
							<div class="badge badge-light" style="font-size: 1.1rem; padding: 8px 12px; border-radius: 20px;" id="utilization-count">0</div>
						</div>
					</div>
				</div>
				
				<div class="card-body p-0">
					<div id="workstation-utilization-table" class="p-3" style="max-height: 500px; overflow-y: auto;">
						<div class="text-center text-muted">
							<i class="fa fa-info-circle mr-2"></i>İş istasyonu doluluk verileri yükleniyor...
						</div>
					</div>
								</div>
			</div>
		`);

		// Tarih filtrelerini ayarla
		const today = new Date();
		const fromDefault = new Date(today.getTime() - (10 * 24 * 60 * 60 * 1000)); // 10 gün önce
		const toDefault = new Date(today.getTime() + (10 * 24 * 60 * 60 * 1000)); // 10 gün sonra

		const fromDateInput = document.getElementById('cutting-from-date');
		const toDateInput = document.getElementById('cutting-to-date');
		
		if (fromDateInput && toDateInput) {
			fromDateInput.value = fromDefault.toISOString().split('T')[0];
			toDateInput.value = toDefault.toISOString().split('T')[0];
		}

		// İlk yükleme
		this.loadCuttingTable();
		
		// İş istasyonu doluluk oranlarını yükle
		this.loadWorkstationUtilization();
	}

	// Kesim planı tablosunu yükle
	async loadCuttingTable() {
		const fromDate = document.getElementById('cutting-from-date')?.value;
		const toDate = document.getElementById('cutting-to-date')?.value;
		const productionType = document.getElementById('cutting-production-type')?.value;

		if (!fromDate || !toDate) return;

		// Cache kontrolü
		const cacheKey = `cutting_${fromDate}_${toDate}_${productionType}`;
		const cachedData = this.dataCache.get(cacheKey);
		const now = Date.now();
		
		if (cachedData && (now - cachedData.timestamp) < (CONFIG.CACHE_DURATION * 2)) {
			this.renderCuttingTable(cachedData.data, productionType);
			return;
		}

		// Loading indicator göster
		this.showTableLoading('cutting');

		try {
			const response = await frappe.call({
				method: "uretim_planlama.uretim_planlama.api.get_daily_cutting_matrix",
				args: { from_date: fromDate, to_date: toDate },
				timeout: 120000 // 2 dakika timeout
			});

			this.hideTableLoading('cutting');

			if (response.exc) {
				this.showError('Kesim planı verileri yüklenirken hata: ' + response.exc);
				return;
			}

			const data = response.message || [];
			
			// Cache'e kaydet
			this.dataCache.set(cacheKey, {
				data: data,
				timestamp: now
			});
			
			this.renderCuttingTable(data, productionType);

		} catch (error) {
			this.hideTableLoading('cutting');
			this.showError('Kesim planı verileri yüklenirken hata: ' + error.message);
		}
	}

	// Loading indicator fonksiyonları
	showTableLoading(tableType) {
		let tbody;
		let message;
		
		switch(tableType) {
			case 'planned':
				tbody = document.getElementById('planlanan-tbody');
				message = 'Planlanan veriler yükleniyor...';
				break;
			case 'unplanned':
				tbody = document.getElementById('planlanmamis-tbody');
				message = 'Planlanmamış veriler yükleniyor...';
				break;
			case 'cutting':
				const container = document.getElementById('cutting-matrix-table');
				if (container) {
					container.innerHTML = `
						<div class="text-center p-4">
							<div class="spinner-border text-primary" role="status">
								<span class="sr-only">Yükleniyor...</span>
							</div>
							<p class="mt-2 text-muted">${message}</p>
						</div>
					`;
				}
				return;
			default:
				return;
		}
		
		if (tbody) {
			tbody.innerHTML = `
				<tr><td colspan="13" class="text-center p-4">
					<div class="spinner-border text-primary" role="status">
						<span class="sr-only">Yükleniyor...</span>
					</div>
					<p class="mt-2 text-muted">${message}</p>
				</td></tr>
			`;
		}
	}

	hideTableLoading(tableType) {
		// Loading indicator'ı gizle - tablo render edildiğinde otomatik temizlenir
	}



	// Kesim planı tablosunu render et
	renderCuttingTable(data, productionType = '') {
		const tableContainer = document.getElementById('cutting-matrix-table');
		if (!tableContainer) return;

		// Üretim türüne göre filtreleme
		let filteredData = data;
		if (productionType === 'pvc') {
			filteredData = data.filter(row => 
				row.workstation && (row.workstation.includes('Murat') || row.workstation.includes('Kaban'))
			);
		} else if (productionType === 'cam') {
			filteredData = data.filter(row => 
				row.workstation && row.workstation.includes('Bottero')
			);
		}

		if (filteredData.length === 0) {
			tableContainer.innerHTML = `
				<div class="text-center text-muted p-4">
					<i class="fa fa-info-circle mr-2"></i>Seçilen tarih aralığında kesim planı bulunamadı
				</div>
			`;
			return;
		}

		// Tarihe göre sırala
		const sortedData = filteredData.sort((a, b) => new Date(a.date) - new Date(b.date));

		// Tablo satırlarını oluştur
		const rows = sortedData.map(row => {
			const totalMtul = parseFloat(row.total_mtul || 0);
			const totalQuantity = parseInt(row.total_quantity || 0);

			// MTUL değerini 1400'e kadar ve 1400 sonrası olarak ayır
			const mtulUnder1400 = Math.min(totalMtul, 1400);
			const mtulOver1400 = totalMtul > 1400 ? totalMtul - 1400 : 0;

			// Verilerle orantılı genişlik hesaplama - 1400 MTUL'e kadar olan kısım daha geniş
			// Maksimum MTUL değeri için ölçeklendirme
			const maxMtul = Math.max(...filteredData.map(item => parseFloat(item.total_mtul || 0)), 2000);
			
			// 1400 MTUL'e kadar olan kısım için daha geniş ölçeklendirme
			// 1400 MTUL = %80 genişlik, 1400+ MTUL = %20 genişlik
			const scaleFactor = 0.8; // 1400 MTUL'e kadar olan kısım için ölçek faktörü
			
			// Segment genişliklerini hesapla
			const under1400Percentage = mtulUnder1400 > 0 ? 
				Math.min((mtulUnder1400 / 1400) * 80, 80) : 0; // 1400 MTUL'e kadar maksimum %80
			const over1400Percentage = mtulOver1400 > 0 ? 
				Math.min((mtulOver1400 / Math.max(maxMtul - 1400, 1)) * 20, 20) : 0; // 1400+ MTUL için %20

			// İş istasyonuna göre renk belirleme
			const baseColor = row.workstation.includes("Kaban") ? '#944de0' : 
							  row.workstation.includes("Murat") ? '#e89225' : '#6c757d';

			// Tarih formatını ayarla
			let displayDate = row.date;
			try {
				const dateObj = new Date(row.date);
				const dayName = dateObj.toLocaleDateString('tr-TR', { weekday: 'long' });
				displayDate = `${dateObj.toLocaleDateString('tr-TR')} (${dayName})`;
			} catch (e) {
				console.warn("Geçersiz tarih:", row.date);
			}

			// Toplam etiketi - daha net görünüm için
			const totalLabel = `${totalMtul.toFixed(2)} MTUL - ${totalQuantity} Adet`;

			return `
				<tr>
					<td style="white-space: nowrap; font-weight: bold; padding: 8px;">${displayDate}</td>
					<td style="color: ${baseColor}; font-weight: bold; padding: 8px;">${row.workstation}</td>
					<td style="padding: 8px;">
						<div style="position: relative; background: #f5f5f5; border: 2px solid #ddd; height: 28px; border-radius: 6px; overflow: hidden; display: flex; align-items: center; min-width: 400px;">
							${mtulUnder1400 > 0 ? `<div style="width: ${under1400Percentage}%; background: ${baseColor}; height: 100%; border-right: 2px solid #fff;"></div>` : ''}
							${mtulOver1400 > 0 ? `<div style="width: ${over1400Percentage}%; background: #dc3545; height: 100%;"></div>` : ''}
							
							<!-- Toplam etiketi - eski düzende -->
							<span style="position: absolute; left: 8px; top: 0; line-height: 28px; font-size: 13px; font-weight: bold; color: #000; text-shadow: 1px 1px 2px #fff;">
								${totalLabel}
							</span>
							${mtulOver1400 > 0 ? `
								<span style="position: absolute; left: ${under1400Percentage}%; top: 0; line-height: 28px; font-size: 13px; font-weight: bold; color: white; text-shadow: 1px 1px 2px #000; padding-left: 4px;">
									+${mtulOver1400.toFixed(2)}
								</span>
							` : ''}
						</div>
					</td>
				</tr>
			`;
		}).join('');

		// Tablo HTML'ini oluştur - daha geniş kolon
		const tableHtml = `
			<table class="table table-bordered table-sm" style="font-size: 13px; width: 100%;">
				<thead class="table-light" style="position: sticky; top: 0; background: #f8f9fa; z-index: 10;">
					<tr>
						<th style="width: 180px; padding: 10px;">Tarih</th>
						<th style="width: 180px; padding: 10px;">İstasyon</th>
						<th style="padding: 10px;">Toplam MTUL / m² - Toplam Adet</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>
		`;

		tableContainer.innerHTML = tableHtml;

		// Count badge'ini güncelle
		const countBadge = document.getElementById('cutting-count');
		if (countBadge) {
			countBadge.textContent = filteredData.length;
		}
	}

		// İş İstasyonu Doluluk Oranları Tablosunu Yükle
	async loadWorkstationUtilization(selectedDate = null) {
		try {
			// Seçilen tarih veya bugünün tarihini al
			const targetDate = selectedDate || new Date();
			const weekStart = this.getMonday(targetDate);
			const weekEnd = new Date(weekStart);
			weekEnd.setDate(weekStart.getDate() + 6);

			const weekStartStr = weekStart.toISOString().split('T')[0];
			const weekEndStr = weekEnd.toISOString().split('T')[0];

			// API'den iş istasyonu doluluk verilerini al
			const response = await frappe.call({
				method: 'uretim_planlama.uretim_planlama.api.get_weekly_production_schedule',
				args: {
					week_start: weekStartStr,
					week_end: weekEndStr
				},
				timeout: 60000
			});

			if (response.exc) {
				console.error('Doluluk verileri yüklenirken hata:', response.exc);
				return;
			}

			const data = response.message;
			if (data && data.workstations) {
				this.renderWorkstationUtilization(data.workstations, data.days, weekStart, weekEnd);
			}

		} catch (error) {
			console.error('İş istasyonu doluluk verileri yüklenirken hata:', error);
		}
	}

	// Pazartesi gününü bul
	getMonday(d) {
		d = new Date(d);
		const day = d.getDay();
		const diff = d.getDate() - day + (day === 0 ? -6 : 1);
		return new Date(d.getFullYear(), d.getMonth(), diff);
	}

	// İş İstasyonu Doluluk Oranları Tablosunu Render Et
	renderWorkstationUtilization(workstations, days, weekStart, weekEnd) {
		const container = document.getElementById('workstation-utilization-table');
		if (!container) return;

		if (!workstations || workstations.length === 0) {
			container.innerHTML = `
				<div class="text-center text-muted p-4">
					<i class="fa fa-info-circle mr-2"></i>İş istasyonu doluluk verisi bulunamadı
				</div>
			`;
			return;
		}

		// Tarih navigasyonu ekle
		const prevWeek = new Date(weekStart);
		prevWeek.setDate(prevWeek.getDate() - 7);
		const nextWeek = new Date(weekStart);
		nextWeek.setDate(nextWeek.getDate() + 7);

		// Haftalık doluluk tablosu oluştur
		let tableHtml = `
			<!-- Sabit Navigasyon ve Tablo -->
			<div style="position: sticky; top: 0; z-index: 1000; background: white; border-bottom: 2px solid #dee2e6;">
				<!-- Tarih Navigasyonu -->
				<div class="d-flex justify-content-between align-items-center" style="background: #f8f9fa; padding: 12px; border-radius: 8px 8px 0 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
					<button class="btn btn-outline-primary btn-sm" onclick="appInstance.loadWorkstationUtilization(new Date('${prevWeek.toISOString()}'))">
						<i class="fa fa-chevron-left mr-1"></i>Önceki Hafta
					</button>
					<div style="display: flex; align-items: center; gap: 15px;">
						<span style="font-weight: 700; color: #2c3e50; font-size: 14px;">
							${weekStart.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })} - ${weekEnd.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })} Tarihleri
						</span>
						<button class="btn btn-outline-success btn-sm" onclick="appInstance.loadWorkstationUtilization()">
							<i class="fa fa-calendar mr-1"></i>Bu Hafta
						</button>
					</div>
					<button class="btn btn-outline-primary btn-sm" onclick="appInstance.loadWorkstationUtilization(new Date('${nextWeek.toISOString()}'))">
						Sonraki Hafta<i class="fa fa-chevron-right ml-1"></i>
					</button>
				</div>
				
				<!-- Tablo -->
				<div class="table-responsive" style="margin: 0;">
					<table class="table table-bordered table-sm mb-0" style="font-size: 12px; width: 100%; background: white; margin: 0;">
						<thead style="background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%); color: white;">
							<tr>
								<th style="width: 120px; padding: 12px; text-align: left; font-weight: 700;">Operasyon</th>
		`;

		// Gün başlıkları - Hafta sonu hariç
		days.forEach(day => {
			const date = new Date(day.date);
			const dayOfWeek = date.getDay(); // 0 = Pazar, 6 = Cumartesi
			
			// Hafta sonu değilse ekle
			if (dayOfWeek !== 0 && dayOfWeek !== 6) {
				const dayName = date.toLocaleDateString('tr-TR', { weekday: 'short' });
				const dateStr = date.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' });
				
				tableHtml += `
					<th style="width: 120px; padding: 8px; text-align: center; font-weight: 700; font-size: 11px;">
						${dayName}<br>${dateStr}
					</th>
				`;
			}
		});

		tableHtml += `
						</tr>
					</thead>
					<tbody>
		`;

		// OPERASYON BAZINDA TOPLAMA
		// operationMap: { [operationName]: { daily: { [weekday]: { plannedMinutes, workMinutes, jobs } } } }
		const operationMap = {};
		workstations.forEach(ws => {
			const ops = ws.operations || [];
			// Her istasyondaki operasyonları kayda al
			ops.forEach(opName => {
				if (!operationMap[opName]) {
					operationMap[opName] = { name: opName, daily: {} };
				}
			});

			// Gün bazında bu operasyonlar için plan ve kapasite biriktir
			days.forEach(day => {
				const date = new Date(day.date);
				const dayOfWeek = date.getDay();
				if (dayOfWeek === 0 || dayOfWeek === 6) return; // Hafta sonu atla
				const weekday = day.weekday; // 'Pazartesi' vb.
				const daySchedule = (ws.schedule?.[weekday] || []).filter(job => job && typeof job === 'object' && job.name && job.duration);

				ops.forEach(opName => {
					const jobsForOp = daySchedule.filter(job => job.operation === opName);
					if (!operationMap[opName].daily[weekday]) {
						operationMap[opName].daily[weekday] = { plannedMinutes: 0, workMinutes: 0, jobs: 0 };
					}
					let planned = 0;
					jobsForOp.forEach(job => { if (typeof job.duration === 'number') planned += job.duration; });
					operationMap[opName].daily[weekday].plannedMinutes += planned;
					operationMap[opName].daily[weekday].jobs += jobsForOp.length;
					// O gün bu operasyondan iş varsa, istasyonun günlük kapasitesini de ekle
					if (jobsForOp.length > 0) {
						const wm = ws.daily_info ? (ws.daily_info[weekday]?.work_minutes || 0) : 0;
						operationMap[opName].daily[weekday].workMinutes += wm;
					}
				});
			});
		});

		// Operasyon satırları
		const operationNames = Object.keys(operationMap).sort();
		operationNames.forEach(opName => {
			tableHtml += `
				<tr style="background: white;">
					<td style="padding: 8px; text-align: left; color: #2c3e50; font-size: 12px; font-weight: 700; border-right: 2px solid #dee2e6;">
						${opName}
					</td>
			`;

			// Günlük doluluk oranları - Hafta sonu hariç
			days.forEach(day => {
				const date = new Date(day.date);
				const dayOfWeek = date.getDay(); // 0 = Pazar, 6 = Cumartesi
				if (dayOfWeek === 0 || dayOfWeek === 6) return;

				const weekday = day.weekday;
				const d = operationMap[opName].daily[weekday] || { plannedMinutes: 0, workMinutes: 0, jobs: 0 };
				let workMinutes = d.workMinutes || 0;
				let plannedMinutes = d.plannedMinutes || 0;

				// Doluluk oranını hesapla - %100'den fazla olabilir
				let doluluk = workMinutes > 0 ? Math.round((plannedMinutes / workMinutes) * 100) : 0;
				doluluk = isNaN(doluluk) ? 0 : Math.max(0, doluluk);
				const overPercent = Math.max(0, doluluk - 100);

				// Renk kodlaması
				let barColor, textColor;
				if (doluluk < 60) {
					barColor = '#28a745';
					textColor = '#155724';
				} else if (doluluk < 90) {
					barColor = '#ffc107';
					textColor = '#856404';
				} else if (doluluk <= 100) {
					barColor = '#dc3545';
					textColor = '#721c24';
				} else {
					barColor = '#dc3545';
					textColor = '#ffffff';
				}

				// Tatil günü kontrolü
				const isHoliday = day.isHoliday;
				if (isHoliday) {
					tableHtml += `
						<td style="padding: 8px; text-align: center; background: #f8f9fa; color: #6c757d; font-size: 11px; border-right: 1px solid #dee2e6;">
							Tatil
						</td>
					`;
				} else {
					tableHtml += `
						<td style="padding: 8px; text-align: center; border-right: 1px solid #dee2e6;">
							<div style="margin-bottom: 4px; font-weight: 700; color: ${textColor}; font-size: 12px;">
								${doluluk}%
								${overPercent > 0 ? `<span class="badge" style="background:#ff9800; color:#fff; margin-left:6px; vertical-align:baseline;">+${overPercent}%</span>` : ''}
							</div>
							<div style="height: 16px; width: 100%; background: #e9ecef; border-radius: 8px; overflow: hidden; position: relative;">
								<div style="width: ${Math.min(doluluk, 100)}%; height: 100%; background: ${barColor}; transition: width 0.5s;"></div>
								${overPercent > 0 ? `<div style=\"position:absolute; right:4px; top:0; height:100%; display:flex; align-items:center; font-size:10px; color:#dc3545; font-weight:700;\">+${overPercent}%</div>` : ''}
							</div>
							<div style="margin-top: 4px; font-size: 10px; color: #6c757d; display:flex; justify-content: space-between; gap:8px;">
								<span><i class="fa fa-clipboard-list" style="color:#17a2b8; margin-right:4px;"></i>${d.jobs} kart</span>
								<span>${Math.floor(plannedMinutes/60)}sa ${plannedMinutes%60}dk</span>
							</div>
						</td>
					`;
				}
			});

			tableHtml += '</tr>';
		});

		tableHtml += `
						</tbody>
					</table>
				</div>
				</div>
			`;

		container.innerHTML = tableHtml;

		// Count badge'ini güncelle (operasyon sayısı)
		const countBadge = document.getElementById('utilization-count');
		if (countBadge) {
			countBadge.textContent = Object.keys(operationMap).length;
		}
	}








	bindEvents() {
		// Planlanan table filter inputs - Anında tepki için
		['opti', 'siparis', 'bayi', 'musteri', 'seri', 'renk', 'tip'].forEach(filter => {
			const element = document.getElementById('planlanan-' + filter + '-filter');
			if (element) {
				element.addEventListener('input', () => {
					this.debouncedLoadPlannedData();
				});
			}
		});
		
		// Planlanan table filter dropdown - Anında tepki için
		const planlananTipFilter = document.getElementById('planlanan-tip-filter');
		if (planlananTipFilter) {
			planlananTipFilter.addEventListener('change', () => {
				this.debouncedLoadPlannedData();
			});
		}
		
		// Planlanmamış table filter inputs - Anında tepki için
		['siparis', 'bayi', 'musteri', 'seri', 'renk', 'tip'].forEach(filter => {
			const element = document.getElementById('planlanmamis-' + filter + '-filter');
			if (element) {
				element.addEventListener('input', () => {
					this.debouncedLoadUnplannedData();
				});
			}
		});
		
		// Planlanmamış table filter dropdowns - Anında tepki için
		['acil', 'tip'].forEach(filter => {
			const element = document.getElementById('planlanmamis-' + filter + '-filter');
			if (element) {
				element.addEventListener('change', () => {
					this.debouncedLoadUnplannedData();
				});
			}
		});
		
		// Toggle completed button - Only affects planned table
		const toggleCompletedBtn = document.getElementById('toggle-completed-btn');
		if (toggleCompletedBtn) {
			toggleCompletedBtn.addEventListener('click', () => {
				this.plannedTable.showCompleted = !this.plannedTable.showCompleted;
				this.renderPlannedTable();
			});
		}
		
		// Planlanan table clear button
		const planlananClearBtn = document.getElementById('planlanan-clear-btn');
		if (planlananClearBtn) {
			planlananClearBtn.addEventListener('click', () => {
				this.clearPlanlananFilters();
				this.loadPlannedData();
			});
		}
		
		// Planlanmamış table clear button
		const planlanmamisClearBtn = document.getElementById('planlanmamis-clear-btn');
		if (planlanmamisClearBtn) {
			planlanmamisClearBtn.addEventListener('click', () => {
				this.clearPlanlanmamisFilters();
				this.loadUnplannedData();
			});
		}
		
		// Refresh button - Kaldırıldı
		// refreshBtn event binding kaldırıldı - kontroller alanı artık yok
		
		// Modal event'leri
		this.bindPlannedTableEvents();
		this.bindUnplannedTableEvents();
		
		// Sıralama event'leri
		this.bindSortingEvents();
		
		// Overview summary events
		this.bindOverviewEvents();

		// Kesim planı tablosu event'leri
		this.bindCuttingTableEvents();

		// Profil Stok Paneli butonu event'i
		const profilStokBtn = document.getElementById('profil-stok-paneli-btn');
		if (profilStokBtn) {
			profilStokBtn.addEventListener('click', () => {
				// Profil Stok Paneli sayfasını yeni sekmede aç
				const url = '/app/profil_stok_paneli';
				window.open(url, '_blank');
			});
		}
	}
	
	bindOverviewEvents() {
		// Overview refresh button - Kaldırıldı (mor header artık yok)

	}

	// Kesim planı tablosu event'leri
	bindCuttingTableEvents() {

		// Tarih filtreleri
		const fromDateInput = document.getElementById('cutting-from-date');
		const toDateInput = document.getElementById('cutting-to-date');
		
		if (fromDateInput) {
			fromDateInput.addEventListener('change', () => {
				this.loadCuttingTable();
			});
		}
		
		if (toDateInput) {
			toDateInput.addEventListener('change', () => {
				this.loadCuttingTable();
			});
		}

		// Üretim türü filtresi
		const productionTypeSelect = document.getElementById('cutting-production-type');
		if (productionTypeSelect) {
			productionTypeSelect.addEventListener('change', () => {
				this.loadCuttingTable();
			});
		}

		// Temizle butonu
		const clearCuttingBtn = document.getElementById('cutting-clear-btn');
		if (clearCuttingBtn) {
			clearCuttingBtn.addEventListener('click', () => {
				if (fromDateInput) fromDateInput.value = '';
				if (toDateInput) toDateInput.value = '';
				if (productionTypeSelect) productionTypeSelect.value = '';
				
				// Varsayılan tarihleri ayarla
				const today = new Date();
				const fromDefault = new Date(today.getTime() - (10 * 24 * 60 * 60 * 1000));
				const toDefault = new Date(today.getTime() + (10 * 24 * 60 * 60 * 1000));
				
				if (fromDateInput) fromDateInput.value = fromDefault.toISOString().split('T')[0];
				if (toDateInput) toDateInput.value = toDefault.toISOString().split('T')[0];
				
				this.loadCuttingTable();
			});
		}
	}
	
	bindSortingEvents() {
		// CSS ekle
		if (!document.getElementById('sorting-styles')) {
			const style = document.createElement('style');
			style.id = 'sorting-styles';
			style.textContent = `
				.sortable-header {
					cursor: pointer;
					user-select: none;
					transition: background-color 0.2s;
				}
				.sortable-header:hover {
					background-color: rgba(255,255,255,0.1) !important;
				}
				.sort-icon {
					font-size: 0.8em;
				}
			`;
			document.head.appendChild(style);
		}
		
		// Event delegation ile tablo sıralama
		document.addEventListener('click', (e) => {
			const header = e.target.closest('.sortable-header');
			if (!header) return;
			
			const column = header.dataset.column;
			if (!column) return;
			
			// Hangi tabloda olduğunu belirle
			const isPlannedTable = header.closest('.table').querySelector('#planlanan-tbody');
			const isUnplannedTable = header.closest('.table').querySelector('#planlanmamis-tbody');
			
			if (isPlannedTable && this.plannedTable.data) {
				const sortedData = utils.tableSorting.sortTable('planned', column, [...this.plannedTable.data]);
				this.plannedTable.data = sortedData;
				this.renderPlannedTable();
				utils.tableSorting.updateSortIcons('planned', column);
			} else if (isUnplannedTable && this.unplannedTable.data) {
				const sortedData = utils.tableSorting.sortTable('unplanned', column, [...this.unplannedTable.data]);
				this.unplannedTable.data = sortedData;
				this.renderUnplannedTable();
				utils.tableSorting.updateSortIcons('unplanned', column);
			}
		});
	}
	
	// Debounce fonksiyonları
	debouncedLoadPlannedData() {
		if (this.debounceTimer) clearTimeout(this.debounceTimer);
		this.debounceTimer = setTimeout(() => {
			this.loadPlannedData();
		}, 500);
	}
	
	debouncedLoadUnplannedData() {
		if (this.debounceTimer) clearTimeout(this.debounceTimer);
		this.debounceTimer = setTimeout(() => {
			this.loadUnplannedData();
		}, 500);
	}

	// Get planlanan filters
	getPlanlananFilters() {
		return {
			opti_no: $('#planlanan-opti-filter').val(),
			siparis_no: $('#planlanan-siparis-filter').val(),
			bayi: $('#planlanan-bayi-filter').val(),
			musteri: $('#planlanan-musteri-filter').val(),
			seri: $('#planlanan-seri-filter').val(),
			renk: $('#planlanan-renk-filter').val(),
			tip: $('#planlanan-tip-filter').val(),
			limit: 200
		};
	}

	// Enhanced filter clear - Array based approach
	clearPlanlananFilters() {
		// Array ile tüm filtreleri temizle
		['opti', 'siparis', 'bayi', 'musteri', 'seri', 'renk', 'tip'].forEach(filter => {
			const element = document.getElementById(`planlanan-${filter}-filter`);
			if (element) {
				element.value = '';
			}
		});
		
		// Toggle state'leri de sıfırla
		const toggleBtn = document.getElementById('toggle-completed-btn');
		if (toggleBtn) {
			this.plannedTable.showCompleted = true;
			this.updatePlannedSummary();
		}
	}

	clearPlanlanmamisFilters() {
		// Array ile tüm filtreleri temizle
		['siparis', 'bayi', 'musteri', 'seri', 'renk', 'acil', 'tip'].forEach(filter => {
			const element = document.getElementById(`planlanmamis-${filter}-filter`);
			if (element) {
				element.value = '';
			}
		});
	}

	getPlanlanmamisFilters() {
		return {
			siparis_no: $('#planlanmamis-siparis-filter').val(),
			bayi: $('#planlanmamis-bayi-filter').val(),
			musteri: $('#planlanmamis-musteri-filter').val(),
			acil_durum: $('#planlanmamis-acil-filter').val(),
			tip: $('#planlanmamis-tip-filter').val(),
			seri: $('#planlanmamis-seri-filter').val(),
			renk: $('#planlanmamis-renk-filter').val()
		};
	}

			// Enhanced renderPlannedTable with grouping
	renderPlannedTable() {
		const tbody = document.getElementById('planlanan-tbody');
		if (!tbody) return;

		if (!this.plannedTable.data || this.plannedTable.data.length === 0) {
			tbody.innerHTML = `
				<tr><td colspan="13" class="text-center text-muted">
					<i class="fa fa-info-circle mr-2"></i>Henüz planlama bulunmuyor
				</td></tr>
			`;
			return;
		}
		
		// Filtreleri al
		const filters = this.getPlanlananFilters();
		
		// Tamamlananları göster/gizle filtresi
		let filteredData = this.plannedTable.data;
		
		if (!this.plannedTable.showCompleted) {
			filteredData = this.plannedTable.data.filter(item => item.plan_status !== 'Completed');
		}
		
		// Performans için sadece ilk 200 kayıt
		if (filteredData.length > 200) {
			filteredData = filteredData.slice(0, 200);
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
					planned_end_date: order.planned_end_date,
					seri: order.seri,
					renk: order.renk,
					plan_status: order.plan_status,
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
			if (order.bayi) optiGroups[optiNo].bayi_list.add(order.bayi);
			if (order.musteri) optiGroups[optiNo].musteri_list.add(order.musteri);
			if (order.seri) optiGroups[optiNo].seri_list.add(order.seri);
			if (order.renk) optiGroups[optiNo].renk_list.add(order.renk);
		});
		
		// Set'leri Array'e çevir
		Object.values(optiGroups).forEach(group => {
			group.bayi_list = Array.from(group.bayi_list);
			group.musteri_list = Array.from(group.musteri_list);
			group.seri_list = Array.from(group.seri_list);
			group.renk_list = Array.from(group.renk_list);
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
			const optiRow = this.createOptiRowElement(optiGroup);
			fragment.appendChild(optiRow);
		});
		
		tbody.innerHTML = '';
		tbody.appendChild(fragment);
		// Event binding sadece bindEvents()'da yapılıyor - duplicate önlemek için
		
		// Update summary after rendering
		this.updatePlannedSummary();
	}

	// Independent event binding methods - Fixed duplicate events
	bindPlannedTableEvents() {
		const tbody = document.getElementById('planlanan-tbody');
		if (!tbody) return;
		
		// Remove existing event listeners to prevent duplicates
		tbody.removeEventListener('click', this.plannedTableClickHandler);
		
		// Create handler function and store reference for removal
		this.plannedTableClickHandler = (e) => {
			const row = e.target.closest('tr[data-opti]');
			if (row && !e.target.closest('button') && !e.target.closest('a')) {
				e.preventDefault();
				e.stopPropagation();
				this.showOptiDetails(row.dataset.opti);
			}
		};
		
		tbody.addEventListener('click', this.plannedTableClickHandler);
	}

	bindUnplannedTableEvents() {
		const tbody = document.getElementById('planlanmamis-tbody');
		if (!tbody) return;

		// Remove existing event listeners to prevent duplicates
		tbody.removeEventListener('click', this.unplannedTableClickHandler);
		
		// Create handler function and store reference for removal
		this.unplannedTableClickHandler = (e) => {
			const row = e.target.closest('tr[data-id]');
			if (row && !e.target.closest('button') && !e.target.closest('a')) {
				e.preventDefault();
				e.stopPropagation();
				this.showOrderDetails(row.dataset.id);
			}
		};
		
		tbody.addEventListener('click', this.unplannedTableClickHandler);
	}

	showOrderDetails(salesOrderId) {
		if (!salesOrderId) return;
		
		// Önceki açık modal'ları hızlıca kapat ve DOM'dan kaldır
		$('.modal:visible').each(function() {
			const currentModal = $(this);
			currentModal.modal('hide');
			// Modal tamamen kapandıktan sonra DOM'dan kaldır
			currentModal.on('hidden.bs.modal', function() {
				currentModal.remove();
			});
		});
		
		// Lazy Loading: Modal'ı sadece açıldığında oluştur
		const modalId = `order-details-${salesOrderId}`;
		let modal = document.getElementById(modalId);
		
		if (!modal) {
			// Modal henüz oluşturulmamış, şimdi oluştur
			modal = $(`
				<div class="modal" id="${modalId}" tabindex="-1" data-backdrop="static" data-keyboard="false">
					<div class="modal-dialog modal-lg">
						<div class="modal-content">
							<div class="modal-header bg-info text-white">
								<h5 class="modal-title">
									<i class="fa fa-info-circle mr-2"></i>Sipariş Detayları - ${salesOrderId}
								</h5>
								<button type="button" class="close text-white" data-dismiss="modal">
									<span>&times;</span>
								</button>
							</div>
							<div class="modal-body">
								<div id="order-details-content-${salesOrderId}">
									<div class="text-center p-4">
										<div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			`);
			
			// Modal'ı DOM'a ekle
			document.body.appendChild(modal[0]);
		}
		
		// Modal'ı hızlıca göster
		modal.modal({
			show: true,
			backdrop: 'static',
			keyboard: false
		});

		// Veriyi sadece modal açıldığında yükle
		const contentDiv = document.getElementById(`order-details-content-${salesOrderId}`);
		if (contentDiv && !contentDiv.dataset.loaded) {
			frappe.call({
				method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_sales_order_details_v2',
				args: { order_no: salesOrderId },
				timeout: 30000, // 30 saniye timeout
				callback: (r) => {
					if (r.exc) {
						errorHandler.show('Sipariş detayları yüklenirken hata: ' + r.exc);
						return;
					}
					
					const data = r.message;
					if (data.error) {
						errorHandler.show(data.error);
						return;
					}
					
					// Veriyi yüklendi olarak işaretle
					contentDiv.dataset.loaded = 'true';
					// Mevcut updateOrderDetailsModal fonksiyonunu kullan
					updateOrderDetailsModal(data);
				},
				error: (err) => {
					errorHandler.show('Bağlantı hatası: ' + err);
				}
			});
		}
	}

	showOptiDetails(optiNo) {
		if (!optiNo) {
			frappe.show_alert({
				message: 'Geçersiz Opti numarası',
				indicator: 'red'
			});
			return;
		}

		// Önce opti detaylarını getir, sipariş detayları modalını aç
		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_opti_details',
			args: { opti_no: optiNo },
			timeout: 30000, // 30 saniye timeout
			callback: (r) => {
				if (r.exc) {
					frappe.show_alert({
						message: 'Opti detayları yüklenemedi: ' + r.exc,
						indicator: 'red'
					});
					return;
				}
				
				if (!r.message) {
					frappe.show_alert({
						message: 'API yanıtı boş',
						indicator: 'red'
					});
					return;
				}
				
				if (r.message.error) {
					frappe.show_alert({
						message: 'API Hatası: ' + r.message.error,
						indicator: 'red'
					});
					return;
				}
				
				if (!r.message.orders || r.message.orders.length === 0) {
					frappe.show_alert({
						message: 'Bu Opti için sipariş bulunamadı: ' + optiNo,
						indicator: 'orange'
					});
					return;
				}

				// Önce Sales Order detayları modalını aç
				this.showSalesOrdersModal(optiNo, r.message.orders);
			},
			error: (err) => {
				frappe.show_alert({
					message: 'Bağlantı hatası: ' + err,
					indicator: 'red'
				});
			}
		});
	}

	showSalesOrdersModal(optiNo, orders) {
		const modalId = 'sales-orders-modal-' + optiNo;
		modalManager.closeOtherModals(modalId);
		
		const modal = modalManager.createModal(
			modalId, 
			`Opti ${optiNo} - Sipariş Detayları`,
			'modal-xl'
		);
		
		if (!modal) return;

		// Üretim planı bilgisini al
		const productionPlan = this.getProductionPlanFromOpti(optiNo);

		// Toplamları hesapla - API field adlarına göre düzelt
		let totalPvc = 0;
		let totalCam = 0;
		let totalMtul = 0;
		
		orders.forEach(order => {
			totalPvc += parseInt(order.pvc_qty || order.pvc_count || 0);
			totalCam += parseInt(order.cam_qty || order.cam_count || 0);
			totalMtul += parseFloat(order.total_mtul || order.toplam_mtul_m2 || 0);
		});

		// Modal içeriğini oluştur - 1. ekrandaki format
		let modalContent = `
			<div class="row mb-3">
				<div class="col-12">
					<div class="alert alert-info d-flex align-items-center">
						<i class="fa fa-info-circle mr-2"></i>
						<div>
							<strong>Opti ${optiNo}</strong><br>
							<small>Toplam ${orders.length} sipariş planlandı</small>
						</div>
					</div>
				</div>
			</div>

			<!-- Özet Kartları -->
			<div class="row mb-4">
				<div class="col-md-4">
					<div class="card bg-danger text-white">
						<div class="card-body text-center">
							<h5 class="card-title">Toplam PVC Adedi</h5>
							<h2 class="mb-0">${totalPvc}</h2>
						</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="card bg-info text-white">
						<div class="card-body text-center">
							<h5 class="card-title">Toplam Cam Adedi</h5>
							<h2 class="mb-0">${totalCam}</h2>
						</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="card bg-success text-white">
						<div class="card-body text-center">
							<h5 class="card-title">Toplam MTÜL/m²</h5>
							<h2 class="mb-0">${totalMtul.toFixed(2)}</h2>
						</div>
					</div>
				</div>
			</div>

			<!-- Filtre Alanları -->
			<div class="row mb-3">
				<div class="col-12">
					<div class="card">
						<div class="card-body p-2">
							<div class="row">
								<div class="col-md-2">
									<input type="text" id="modal-siparis-filter" class="form-control form-control-sm" placeholder="Sipariş No...">
								</div>
								<div class="col-md-2">
									<input type="text" id="modal-bayi-filter" class="form-control form-control-sm" placeholder="Bayi...">
								</div>
								<div class="col-md-2">
									<input type="text" id="modal-musteri-filter" class="form-control form-control-sm" placeholder="Müşteri...">
								</div>
								<div class="col-md-2">
									<input type="text" id="modal-seri-filter" class="form-control form-control-sm" placeholder="Seri...">
								</div>
								<div class="col-md-2">
									<input type="text" id="modal-renk-filter" class="form-control form-control-sm" placeholder="Renk...">
								</div>
								<div class="col-md-2">
									<button type="button" id="modal-clear-filters" class="btn btn-sm btn-danger">
										<i class="fa fa-times"></i> Temizle
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Sipariş Detayları Başlığı -->
			<div class="row mb-3">
				<div class="col-12">
					<h6 class="mb-0 d-flex align-items-center">
						<i class="fa fa-list mr-2"></i>
						Sipariş Detayları
					</h6>
				</div>
			</div>

			<!-- Sipariş Tablosu -->
			<div class="table-responsive">
				<table class="table table-sm" style="background: white;">
					<thead style="background: #007bff; color: white;">
						<tr>
							<th style="padding: 8px;">Sipariş No</th>
							<th style="padding: 8px;">Bayi</th>
							<th style="padding: 8px;">Müşteri</th>
							<th style="padding: 8px;">Seri</th>
							<th style="padding: 8px;">Renk</th>
							<th style="padding: 8px;">Adet</th>
							<th style="padding: 8px;">MTÜL/m²</th>
							<th style="padding: 8px;">Durum & Açıklama</th>
							<th style="padding: 8px;">İşlemler</th>
						</tr>
					</thead>
					<tbody style="background: white;">
		`;

		orders.forEach(order => {
			// API'den gelen field adları - Python API'sine göre düzelt
			const siparisDate = order.siparis_tarihi ? utils.formatDate(order.siparis_tarihi) : '-';
			const deliveryDate = order.bitis_tarihi ? utils.formatDate(order.bitis_tarihi) : '-';
			const pvcCount = parseInt(order.pvc_qty || order.pvc_count || 0);
			const camCount = parseInt(order.cam_qty || order.cam_count || 0);
			const mtul = parseFloat(order.total_mtul || order.toplam_mtul_m2 || 0);
			const seri = order.seri || order.series || '-';
			const renk = order.renk || order.color || '-';
			const remarks = order.siparis_aciklama || order.custom_remarks || order.remarks || '';
			const bayi = order.bayi || order.customer_name || '-';
			const musteri = order.musteri || order.customer || '-';
			const itemCount = order.item_count || 1; // Bu siparişteki toplam ürün sayısı
			
			// Profil ve Cam badge'leri
			let profileBadge = '';
			let camBadge = '';
			
			if (pvcCount > 0) {
				profileBadge = `<span class="badge" style="background: #dc3545; color: white; margin-right: 2px;">${pvcCount} Profil</span>`;
			}
			if (camCount > 0) {
				camBadge = `<span class="badge" style="background: #007bff; color: white;">${camCount} Cam</span>`;
			}
			
			// Seri ve Renk badge'leri - 1. ekrandaki gibi
			const seriBadge = seri !== '-' ? `<span class="badge" style="background: #17a2b8; color: white; margin-right: 5px;">${seri}</span>` : '';
			const renkBadge = renk !== '-' ? `<span class="badge" style="background: #ffc107; color: black;">${renk}</span>` : '';
			
			// Durum badge - order.is_urgent kontrolü
			const isUrgent = order.is_urgent || order.custom_acil_durum || false;
			const durumBadge = isUrgent ? 
				`<span class="badge" style="background: #dc3545; color: white; margin-bottom: 5px;"><i class="fa fa-exclamation-triangle"></i> ACİL</span>` :
				`<span class="badge" style="background: #28a745; color: white; margin-bottom: 5px;"><i class="fa fa-check"></i> NORMAL</span>`;
			
			modalContent += `
				<tr class="cursor-pointer sales-order-row" data-sales-order="${order.sales_order}" style="background: white;">
					<td style="padding: 8px;">
						<strong style="color: #17a2b8;">${order.sales_order}</strong>
						<br><small style="color: #6c757d;">${siparisDate}</small>
					</td>
					<td style="padding: 8px;">${utils.escapeHtml(bayi)}</td>
					<td style="padding: 8px;">
						<strong>${utils.escapeHtml(musteri)}</strong>
					</td>
					<td style="padding: 8px;">${seriBadge}</td>
					<td style="padding: 8px;">${renkBadge}</td>
					<td style="padding: 8px;">
						${profileBadge}
						${camBadge}
					</td>
					<td style="padding: 8px;">
						<span class="badge" style="background: #28a745; color: white;">${mtul.toFixed(2)}</span>
					</td>
					<td style="padding: 8px;">
						${durumBadge}
						${remarks ? `<br><small style="color: #6c757d;">${utils.escapeHtml(remarks)}</small>` : ''}
					</td>
					<td style="padding: 8px;">
						<div class="btn-group-vertical" style="width: 100%;">
							<button class="btn btn-sm sales-order-btn" data-sales-order="${order.sales_order}" 
								style="background: #28a745; color: white; border: none; margin-bottom: 2px; font-size: 11px;">
								<i class="fa fa-external-link mr-1"></i>Sipariş
							</button>
							<button class="btn btn-sm work-orders-btn" data-sales-order="${order.sales_order}" 
								style="background: #ffc107; color: black; border: none; font-size: 11px;">
								<i class="fa fa-cogs mr-1"></i>İş Emirleri
							</button>
						</div>
					</td>
				</tr>
			`;
		});

		modalContent += `
					</tbody>
				</table>
			</div>
		`;

		// Modal header'ını güncelle - siyah yerine kırmızı
		modal.find('.modal-header').css({
			'background': '#dc3545',
			'color': 'white',
			'border': 'none'
		});

		// Modal body'yi beyaz yap
		modal.find('.modal-body').css({
			'background': 'white',
			'color': '#333'
		});

		// Modal content'i beyaz yap
		modal.find('.modal-content').css({
			'background': 'white',
			'border': 'none'
		});

		// Modal içeriğini güncelle
		const contentDiv = modal.find(`#modal-content-${modalId}`);
		contentDiv.html(modalContent);

		// Event listener'ları ekle
		// Sipariş butonu - Satış siparişi formunu yeni pencerede aç
		modal.find('.sales-order-btn').on('click', function(e) {
			e.preventDefault();
			e.stopPropagation();
			const salesOrder = $(this).data('sales-order');
			// Modal'ı kapat ve satış siparişi formunu yeni pencerede aç
			modal.modal('hide');
			setTimeout(() => {
				const url = `/app/sales-order/${salesOrder}`;
				window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
			}, 300);
		});

		// İş Emirleri butonu - İş emirlerini göster
		modal.find('.work-orders-btn').on('click', function(e) {
			e.preventDefault();
			e.stopPropagation();
			const salesOrder = $(this).data('sales-order');
			// Modal'ı kapat ve iş emirlerini göster
			modal.modal('hide');
			setTimeout(() => {
				// Üretim planı bilgisini geç
				window.showWorkOrdersPaneli(salesOrder, productionPlan);
			}, 300);
		});

		// Satıra tıklama event'i - iş emirlerini göster
		modal.find('.sales-order-row').on('click', function(e) {
			if (!$(e.target).hasClass('work-orders-btn') && !$(e.target).closest('.work-orders-btn').length &&
				!$(e.target).hasClass('sales-order-btn') && !$(e.target).closest('.sales-order-btn').length) {
				const salesOrder = $(this).data('sales-order');
				// Modal'ı kapat ve iş emirlerini göster
				modal.modal('hide');
				setTimeout(() => {
					// Üretim planı bilgisini geç
					window.showWorkOrdersPaneli(salesOrder, productionPlan);
				}, 300);
			}
		});

		// Modal filtre event'lerini ekle
		this.bindModalFilters(modal, orders);
	}

	// Üretim planı bilgisini Opti numarasından al
	getProductionPlanFromOpti(optiNo) {
		if (!optiNo || !this.plannedTable.data) return null;
		
		// Planlanan verilerde bu Opti numarasına ait üretim planını bul
		const optiData = this.plannedTable.data.find(item => item.opti_no === optiNo);
		return optiData ? optiData.uretim_plani : null;
	}



	// Modal filtre fonksiyonları
	bindModalFilters(modal, orders) {
		const originalOrders = [...orders]; // Orijinal veriyi kopyala
		
		// Filtre input'ları
		const siparisFilter = modal.find('#modal-siparis-filter');
		const bayiFilter = modal.find('#modal-bayi-filter');
		const musteriFilter = modal.find('#modal-musteri-filter');
		const seriFilter = modal.find('#modal-seri-filter');
		const renkFilter = modal.find('#modal-renk-filter');
		const clearFiltersBtn = modal.find('#modal-clear-filters');
		
		// Filtre fonksiyonu
		const applyFilters = () => {
			const siparisValue = siparisFilter.val().toLowerCase();
			const bayiValue = bayiFilter.val().toLowerCase();
			const musteriValue = musteriFilter.val().toLowerCase();
			const seriValue = seriFilter.val().toLowerCase();
			const renkValue = renkFilter.val().toLowerCase();
			
			const filteredOrders = originalOrders.filter(order => {
				const siparisMatch = !siparisValue || order.sales_order.toLowerCase().includes(siparisValue);
				const bayiMatch = !bayiValue || (order.bayi && order.bayi.toLowerCase().includes(bayiValue));
				const musteriMatch = !musteriValue || (order.musteri && order.musteri.toLowerCase().includes(musteriValue));
				const seriMatch = !seriValue || (order.seri && order.seri.toLowerCase().includes(seriValue));
				const renkMatch = !renkValue || (order.renk && order.renk.toLowerCase().includes(renkValue));
				
				return siparisMatch && bayiMatch && musteriMatch && seriMatch && renkMatch;
			});
			
			// Filtrelenmiş verileri tabloda göster
			this.renderFilteredModalTable(modal, filteredOrders);
		};
		
		// Input event'leri
		[siparisFilter, bayiFilter, musteriFilter, seriFilter, renkFilter].forEach(input => {
			input.on('input', applyFilters);
		});
		
		// Temizle butonu
		clearFiltersBtn.on('click', () => {
			siparisFilter.val('');
			bayiFilter.val('');
			musteriFilter.val('');
			seriFilter.val('');
			renkFilter.val('');
			applyFilters();
		});
	}
	
	// Filtrelenmiş modal tablosunu render et
	renderFilteredModalTable(modal, filteredOrders) {
		const tbody = modal.find('tbody');
		if (!tbody.length) return;
		
		// Tabloyu temizle
		tbody.empty();
		
		// Filtrelenmiş verileri ekle
		filteredOrders.forEach(order => {
			const siparisDate = order.siparis_tarihi ? utils.formatDate(order.siparis_tarihi) : '-';
			const pvcCount = parseInt(order.pvc_qty || order.pvc_count || 0);
			const camCount = parseInt(order.cam_qty || order.cam_count || 0);
			const mtul = parseFloat(order.total_mtul || order.toplam_mtul_m2 || 0);
			const seri = order.seri || order.series || '-';
			const renk = order.renk || order.color || '-';
			const remarks = order.siparis_aciklama || order.custom_remarks || order.remarks || '';
			const bayi = order.bayi || order.customer_name || '-';
			const musteri = order.musteri || order.customer || '-';
			
			// Profil ve Cam badge'leri
			let profileBadge = '';
			let camBadge = '';
			
			if (pvcCount > 0) {
				profileBadge = `<span class="badge" style="background: #dc3545; color: white; margin-right: 2px;">${pvcCount} Profil</span>`;
			}
			if (camCount > 0) {
				camBadge = `<span class="badge" style="background: #007bff; color: white;">${camCount} Cam</span>`;
			}
			
			// Seri ve Renk badge'leri
			const seriBadge = seri !== '-' ? `<span class="badge" style="background: #17a2b8; color: white; margin-right: 5px;">${seri}</span>` : '';
			const renkBadge = renk !== '-' ? `<span class="badge" style="background: #ffc107; color: black;">${renk}</span>` : '';
			
			// Durum badge
			const isUrgent = order.is_urgent || order.custom_acil_durum || false;
			const durumBadge = isUrgent ? 
				`<span class="badge" style="background: #dc3545; color: white; margin-bottom: 5px;"><i class="fa fa-exclamation-triangle"></i> ACİL</span>` :
				`<span class="badge" style="background: #28a745; color: white; margin-bottom: 5px;"><i class="fa fa-check"></i> NORMAL</span>`;
			
			const row = `
				<tr class="cursor-pointer sales-order-row" data-sales-order="${order.sales_order}" style="background: white;">
					<td style="padding: 8px;">
						<strong style="color: #17a2b8;">${order.sales_order}</strong>
						<br><small style="color: #6c757d;">${siparisDate}</small>
					</td>
					<td style="padding: 8px;">${utils.escapeHtml(bayi)}</td>
					<td style="padding: 8px;">
						<strong>${utils.escapeHtml(musteri)}</strong>
					</td>
					<td style="padding: 8px;">${seriBadge}</td>
					<td style="padding: 8px;">${renkBadge}</td>
					<td style="padding: 8px;">
						${profileBadge}
						${camBadge}
					</td>
					<td style="padding: 8px;">
						<span class="badge" style="background: #28a745; color: white;">${mtul.toFixed(2)}</span>
					</td>
					<td style="padding: 8px;">
						${durumBadge}
						${remarks ? `<br><small style="color: #6c757d;">${utils.escapeHtml(remarks)}</small>` : ''}
					</td>
					<td style="padding: 8px;">
						<div class="btn-group-vertical" style="width: 100%;">
							<button class="btn btn-sm sales-order-btn" data-sales-order="${order.sales_order}" 
								style="background: #28a745; color: white; border: none; margin-bottom: 2px; font-size: 11px;">
								<i class="fa fa-external-link mr-1"></i>Sipariş
							</button>
							<button class="btn btn-sm work-orders-btn" data-sales-order="${order.sales_order}" 
								style="background: #ffc107; color: black; border: none; font-size: 11px;">
								<i class="fa fa-cogs mr-1"></i>İş Emirleri
							</button>
						</div>
					</td>
				</tr>
			`;
			
			tbody.append(row);
		});
		
		// Event listener'ları yeniden bağla
		this.bindModalRowEvents(modal);
	}
	
	// Modal satır event'lerini bağla
	bindModalRowEvents(modal) {
		// Sipariş butonu - Satış siparişi formunu yeni pencerede aç
		modal.find('.sales-order-btn').off('click').on('click', function(e) {
			e.preventDefault();
			e.stopPropagation();
			const salesOrder = $(this).data('sales-order');
			modal.modal('hide');
			setTimeout(() => {
				const url = `/app/sales-order/${salesOrder}`;
				window.open(url, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
			}, 300);
		});

		// İş Emirleri butonu - İş emirlerini göster
		modal.find('.work-orders-btn').off('click').on('click', function(e) {
			e.preventDefault();
			e.stopPropagation();
			const salesOrder = $(this).data('sales-order');
			modal.modal('hide');
			setTimeout(() => {
				// Üretim planı bilgisini geç
				window.showWorkOrdersPaneli(salesOrder, productionPlan);
			}, 300);
		});
		
		modal.find('.sales-order-row').off('click').on('click', function(e) {
			if (!$(e.target).hasClass('work-orders-btn') && !$(e.target).closest('.work-orders-btn').length && 
				!$(e.target).hasClass('sales-order-btn') && !$(e.target).closest('.sales-order-btn').length) {
				const salesOrder = $(this).data('sales-order');
				modal.modal('hide');
				setTimeout(() => {
					// Üretim planı bilgisini geç
					window.showWorkOrdersPaneli(salesOrder, productionPlan);
				}, 300);
			}
		});
	}

	// === OVERVIEW SUMMARY TABLE METHODS (BAĞIMSIZ) ===
	
	async loadOverviewSummaryData() {
		try {
			// Her iki tablodan veri topla
			const plannedData = this.plannedTable.data || [];
			const unplannedData = this.unplannedTable.data || [];
			
			// Sadece PVC-CAM yan yana tablosunu güncelle
			this.renderPvcCamOverview(plannedData, unplannedData);
			
		} catch (error) {
			console.error('Overview summary yükleme hatası:', error);
			console.log('PVC-CAM tablosu güncellenirken hata oluştu:', error);
		}
	}
	
	updateOverviewStats(plannedData, unplannedData) {
		// Sadece PVC-CAM tablosu için gerekli - 6 kart kaldırıldı
		// Bu fonksiyon artık boş çünkü üst kartlar kaldırıldı
		console.log('Overview stats güncellemesi - sadece PVC-CAM tablosu aktif');
	}
	
	// generateWeeklyOverview fonksiyonu kaldırıldı - haftalık tablo artık yok
	
	renderPvcCamOverview(plannedData, unplannedData) {
		// PVC hesaplamaları
		const pvcData = this.calculatePvcOverview(plannedData, unplannedData);
		const camData = this.calculateCamOverview(plannedData, unplannedData);
		
		// PVC verilerini güncelle
		document.getElementById('pvc-adet').textContent = pvcData.adet || '0';
		document.getElementById('pvc-mtul').textContent = pvcData.mtul || '0';
		document.getElementById('pvc-gunluk').textContent = pvcData.gunlukOrtalama || '0';
		document.getElementById('pvc-gun-sayisi').textContent = pvcData.gunSayisi || '0';
		document.getElementById('pvc-bitis-tarihi').textContent = pvcData.bitisTarihi || '-';
		
		// CAM verilerini güncelle
		document.getElementById('cam-adet').textContent = camData.adet || '0';
		document.getElementById('cam-m2').textContent = camData.m2 || '0';
		document.getElementById('cam-gunluk').textContent = camData.gunlukOrtalama || '0';
		document.getElementById('cam-gun-sayisi').textContent = camData.gunSayisi || '0';
		document.getElementById('cam-bitis-tarihi').textContent = camData.bitisTarihi || '-';
	}
	
	calculatePvcOverview(plannedData, unplannedData) {
		// MANTIK: Onaylı Toplam Siparişler - Tamamlanan Siparişler = Kalan PVC
		
		let toplamOnayliPvcAdet = 0;
		let toplamOnayliPvcMtul = 0;
		let tamamlananPvcAdet = 0;
		let tamamlananPvcMtul = 0;
		
		// 1. Planlanan verilerden: Onaylı toplam ve tamamlanan ayrı hesapla
		plannedData.forEach(item => {
			const pvcQty = parseFloat(item.pvc_qty || 0);
			const totalMtul = parseFloat(item.total_mtul || 0);
			const pvcRatio = pvcQty / (pvcQty + parseFloat(item.cam_qty || 0) || 1);
			const pvcMtul = totalMtul * pvcRatio;
			
			// Toplam onaylı PVC
			toplamOnayliPvcAdet += pvcQty;
			toplamOnayliPvcMtul += pvcMtul;
			
			// Tamamlanan PVC (durum: Completed veya %100)
			if (item.durum === 'Completed' || parseFloat(item.tamamlanma_yuzdesi || 0) >= 100) {
				tamamlananPvcAdet += pvcQty;
				tamamlananPvcMtul += pvcMtul;
			}
		});
		
		// 2. Planlanmamış verilerden: Sadece onaylı toplama ekle (henüz tamamlanmamış)
		unplannedData.forEach(item => {
			if (item.item_type === 'PVC' || parseFloat(item.pvc_count || 0) > 0) {
				toplamOnayliPvcAdet += parseFloat(item.pvc_count || 0);
				toplamOnayliPvcMtul += parseFloat(item.total_mtul || 0);
			}
		});
		
		// 3. Kalan PVC = Toplam Onaylı - Tamamlanan
		const kalanPvcAdet = toplamOnayliPvcAdet - tamamlananPvcAdet;
		const kalanPvcMtul = toplamOnayliPvcMtul - tamamlananPvcMtul;
		
		// 4. Hesaplamalar
		const gunlukOrtalama = 120;
		const gunSayisi = kalanPvcAdet > 0 ? (kalanPvcAdet / gunlukOrtalama).toFixed(1) : '0';
		
		// Tahmini bitiş tarihi hesaplama: BUGÜN + 6 + PVC ÜRETİM GÜN SAYISI
		const bugun = new Date();
		const toplamGun = 6 + parseFloat(gunSayisi); // 6 gün + üretim gün sayısı
		const bitisTarihi = new Date(bugun.getTime() + (toplamGun * 24 * 60 * 60 * 1000));
		const formatliTarih = bitisTarihi.toLocaleDateString('tr-TR');
		
		return {
			adet: Math.round(kalanPvcAdet),
			mtul: Math.round(kalanPvcMtul),
			gunlukOrtalama: gunlukOrtalama,
			gunSayisi: gunSayisi,
			bitisTarihi: formatliTarih
		};
	}
	
	calculateCamOverview(plannedData, unplannedData) {
		// MANTIK: Onaylı Toplam Siparişler - Tamamlanan Siparişler = Kalan CAM
		
		let toplamOnayliCamAdet = 0;
		let toplamOnayliCamM2 = 0;
		let tamamlananCamAdet = 0;
		let tamamlananCamM2 = 0;
		
		// 1. Planlanan verilerden: Onaylı toplam ve tamamlanan ayrı hesapla
		plannedData.forEach(item => {
			const camQty = parseFloat(item.cam_qty || 0);
			const camM2 = camQty * 0.95; // Ortalama 0.95 m2/adet
			
			// Toplam onaylı CAM
			toplamOnayliCamAdet += camQty;
			toplamOnayliCamM2 += camM2;
			
			// Tamamlanan CAM (durum: Completed veya %100)
			if (item.durum === 'Completed' || parseFloat(item.tamamlanma_yuzdesi || 0) >= 100) {
				tamamlananCamAdet += camQty;
				tamamlananCamM2 += camM2;
			}
		});
		
		// 2. Planlanmamış verilerden: Sadece onaylı toplama ekle (henüz tamamlanmamış)
		unplannedData.forEach(item => {
			if (item.item_type === 'CAM' || parseFloat(item.cam_count || 0) > 0) {
				const camCount = parseFloat(item.cam_count || 0);
				const camM2 = camCount * 0.95;
				
				toplamOnayliCamAdet += camCount;
				toplamOnayliCamM2 += camM2;
			}
		});
		
		// 3. Kalan CAM = Toplam Onaylı - Tamamlanan
		const kalanCamAdet = toplamOnayliCamAdet - tamamlananCamAdet;
		const kalanCamM2 = toplamOnayliCamM2 - tamamlananCamM2;
		
		// 4. Hesaplamalar
		const gunlukOrtalama = 350;
		const gunSayisi = kalanCamAdet > 0 ? (kalanCamAdet / gunlukOrtalama).toFixed(1) : '0';
		
		// Tahmini bitiş tarihi hesaplama: BUGÜN + 6 + CAM ÜRETİM GÜN SAYISI
		const bugun = new Date();
		const toplamGun = 6 + parseFloat(gunSayisi); // 6 gün + üretim gün sayısı
		const bitisTarihi = new Date(bugun.getTime() + (toplamGun * 24 * 60 * 60 * 1000));
		const formatliTarih = bitisTarihi.toLocaleDateString('tr-TR');
		
		return {
			adet: Math.round(kalanCamAdet),
			m2: Math.round(kalanCamM2),
			gunlukOrtalama: gunlukOrtalama,
			gunSayisi: gunSayisi,
			bitisTarihi: formatliTarih
		};
	}
	
	// showOverviewError fonksiyonu kaldırıldı - artık haftalık tablo yok

	// Legacy summary methods (eski planlanan tablo için)
	generateSummaryData(plannedData) {
		if (!plannedData || !Array.isArray(plannedData) || plannedData.length === 0) {
			return [];
		}
		
		// Haftalara göre grupla
		const weeklyData = {};
		
		plannedData.forEach(item => {
			const week = item.hafta || 'Bilinmiyor';
			
			if (!weeklyData[week]) {
				weeklyData[week] = {
					hafta: week,
					opti_count: new Set(),
					siparis_count: new Set(),
					total_pvc: 0,
					total_cam: 0,
					total_mtul: 0,
					completed_items: 0,
					total_items: 0
				};
			}
			
			const group = weeklyData[week];
			
			// Unique sayımlar
			if (item.opti_no) group.opti_count.add(item.opti_no);
			if (item.sales_order) group.siparis_count.add(item.sales_order);
			
			// Toplamlar
			group.total_pvc += parseFloat(item.pvc_qty || 0);
			group.total_cam += parseFloat(item.cam_qty || 0);
			group.total_mtul += parseFloat(item.total_mtul || 0);
			group.total_items += 1;
			
			// Tamamlanma durumu
			if (item.durum === 'Completed' || item.tamamlanma_yuzdesi >= 100) {
				group.completed_items += 1;
			}
		});
		
		// Array'e çevir ve hesapla
		return Object.values(weeklyData).map(group => ({
			hafta: group.hafta,
			opti_sayisi: group.opti_count.size,
			siparis_sayisi: group.siparis_count.size,
			toplam_pvc: group.total_pvc,
			toplam_cam: group.total_cam,
			toplam_mtul: Math.round(group.total_mtul * 100) / 100,
			tamamlanma_yuzdesi: group.total_items > 0 ? Math.round((group.completed_items / group.total_items) * 100) : 0,
			durum: group.completed_items === group.total_items ? 'Tamamlandı' : 
				   group.completed_items === 0 ? 'Başlanmadı' : 'Devam Ediyor'
		})).sort((a, b) => {
			// Hafta sıralaması - güvenli string kontrolü
			const haftaA = String(a.hafta || '');
			const haftaB = String(b.hafta || '');
			
			if (haftaA === 'Bilinmiyor') return 1;
			if (haftaB === 'Bilinmiyor') return -1;
			
			// String değilse veya boşsa en sona koy
			if (!haftaA || typeof haftaA !== 'string') return 1;
			if (!haftaB || typeof haftaB !== 'string') return -1;
			
			return haftaA.localeCompare(haftaB);
		});
	}
	
	renderSummaryTable(summaryData) {
		const tbody = document.getElementById('summary-tbody');
		if (!tbody) return;
		
		if (!summaryData || summaryData.length === 0) {
			tbody.innerHTML = `
				<tr>
					<td colspan="8" class="text-center text-muted" style="padding: 20px;">
						<i class="fa fa-info-circle mr-2"></i>Özet veri bulunmuyor
					</td>
				</tr>
			`;
			return;
		}
		
		let html = '';
		summaryData.forEach(item => {
			const durumBadge = item.durum === 'Tamamlandı' ? 'badge-success' :
							  item.durum === 'Devam Ediyor' ? 'badge-warning' : 'badge-secondary';
			
			const progressColor = item.tamamlanma_yuzdesi >= 100 ? 'success' :
								  item.tamamlanma_yuzdesi >= 75 ? 'info' :
								  item.tamamlanma_yuzdesi >= 50 ? 'warning' : 'danger';
			
			html += `
				<tr style="background: white;">
					<td style="padding: 8px; text-align: center; font-weight: 600;">${item.hafta}</td>
					<td style="padding: 8px; text-align: center;">${item.opti_sayisi}</td>
					<td style="padding: 8px; text-align: center;">${item.siparis_sayisi}</td>
					<td style="padding: 8px; text-align: center; color: #dc3545; font-weight: 600;">${item.toplam_pvc}</td>
					<td style="padding: 8px; text-align: center; color: #007bff; font-weight: 600;">${item.toplam_cam}</td>
					<td style="padding: 8px; text-align: center; color: #28a745; font-weight: 600;">${item.toplam_mtul}</td>
					<td style="padding: 8px; text-align: center;">
						<div class="progress" style="height: 18px; margin: 0;">
							<div class="progress-bar bg-${progressColor}" style="width: ${item.tamamlanma_yuzdesi}%;">
								${item.tamamlanma_yuzdesi}%
							</div>
						</div>
					</td>
					<td style="padding: 8px; text-align: center;">
						<span class="badge ${durumBadge} badge-sm">${item.durum}</span>
					</td>
				</tr>
			`;
		});
		
		tbody.innerHTML = html;
	}

	// Independent table data loading methods
	async loadPlannedData() {
		if (this.plannedTable.isLoading) return;
		
		this.plannedTable.isLoading = true;
		
		try {
			const filters = this.getPlanlananFilters();
			const cacheKey = `planned_${JSON.stringify(filters)}`;
			const cachedData = this.dataCache.get(cacheKey);
			const now = Date.now();
			
			// Cache kontrolü - daha uzun süre cache'de tut
			if (cachedData && (now - cachedData.timestamp) < (CONFIG.CACHE_DURATION * 3)) {
				this.plannedTable.data = cachedData.data;
				this.renderPlannedTable();
				this.updatePlannedSummary();
				
				// Özet tabloyu güncelle (cache'li veri için)
				const summaryData = this.generateSummaryData(this.plannedTable.data);
				this.renderSummaryTable(summaryData);
				
				// Overview summary'yi güncelle
				this.loadOverviewSummaryData();
				
				this.plannedTable.isLoading = false;
				return;
			}
			
			// Loading indicator göster
			this.showTableLoading('planned');
			
			const apiCall = frappe.call({
				method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_production_planning_data',
				args: { filters: JSON.stringify(filters) },
				timeout: 120000, // 2 dakika timeout
				callback: (r) => {
					this.plannedTable.isLoading = false;
					this.hideTableLoading('planned');
					
					if (r.exc) {
						this.showError('Planlanan veri yüklenirken hata: ' + r.exc);
						return;
					}
					
					const data = r.message;
					
					if (data.error) {
						this.showError(data.error);
						return;
					}
					
					this.plannedTable.data = data.planned || [];
					
					// Cache'e kaydet - daha uzun süre
					this.dataCache.set(cacheKey, {
						data: this.plannedTable.data,
						timestamp: now
					});
					
					this.renderPlannedTable();
					this.updatePlannedSummary();
					
					// Özet tabloyu güncelle
					const summaryData = this.generateSummaryData(this.plannedTable.data);
					this.renderSummaryTable(summaryData);
					
					// Overview summary'yi güncelle
					this.loadOverviewSummaryData();
				},
				error: (err) => {
					this.plannedTable.isLoading = false;
					this.hideTableLoading('planned');
					this.showError('Planlanan veri bağlantı hatası: ' + err);
				}
			});

			// setTimeout(() => {
			// 	if (this.plannedTable.isLoading) {
			// 		this.plannedTable.isLoading = false;
			// 		this.hideTableLoading('planned');
			// 		this.showError('Planlanan veri yükleme zaman aşımı.');
			// 	}
			// }, 61000);
			
		} catch (error) {
			this.plannedTable.isLoading = false;
			this.hideTableLoading('planned');
			this.showError('Planlanan veriler yüklenirken hata oluştu: ' + error.message);
		}
	}

	async loadUnplannedData() {
		if (this.unplannedTable.isLoading) return;
		
		this.unplannedTable.isLoading = true;
		
		try {
			const filters = this.getPlanlanmamisFilters();
			const cacheKey = `unplanned_${JSON.stringify(filters)}`;
			const cachedData = this.dataCache.get(cacheKey);
			const now = Date.now();
			
			// Cache kontrolü - daha uzun süre cache'de tut
			if (cachedData && (now - cachedData.timestamp) < (CONFIG.CACHE_DURATION * 3)) {
				this.unplannedTable.data = cachedData.data;
				this.renderUnplannedTable();
				this.updateUnplannedSummary();
				
				// Overview summary'yi güncelle (cache'li unplanned veri için)
				this.loadOverviewSummaryData();
				
				this.unplannedTable.isLoading = false;
				return;
			}
			
			// Loading indicator göster
			this.showTableLoading('unplanned');
			
			const apiCall = frappe.call({
				method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_unplanned_data',
				args: { filters: JSON.stringify(filters) },
				timeout: 60000, // 60 saniye timeout
				callback: (r) => {
					this.unplannedTable.isLoading = false;
					this.hideTableLoading('unplanned');
					
					if (r.exc) {
						this.showError('Planlanan veri yüklenirken hata: ' + r.exc);
						return;
					}
					
					const data = r.message;
					
					if (data.error) {
						this.showError(data.error);
						return;
					}
					
					this.unplannedTable.data = data.unplanned || [];
					
					// Cache'e kaydet - daha uzun süre
					this.dataCache.set(cacheKey, {
						data: this.unplannedTable.data,
						timestamp: now
					});
					
					this.renderUnplannedTable();
					this.updateUnplannedSummary();
					
					// Overview summary'yi güncelle (yeni unplanned veri için)
					this.loadOverviewSummaryData();
				},
				error: (err) => {
					this.unplannedTable.isLoading = false;
					this.hideTableLoading('unplanned');
					this.showError('Planlanmamış veri bağlantı hatası: ' + err);
				}
			});

			// setTimeout(() => {
			// 	if (this.unplannedTable.isLoading) {
			// 		this.unplannedTable.isLoading = false;
			// 		this.hideTableLoading('unplanned');
			// 		this.showError('Planlanmamış veri yükleme zaman aşımı.');
			// 	}
			// }, 61000);
			
		} catch (error) {
			this.unplannedTable.isLoading = false;
			this.hideTableLoading('unplanned');
			this.showError('Planlanmamış veriler yüklenirken hata oluştu: ' + error.message);
		}
	}

	// Legacy method for backward compatibility
	async loadProductionData(filters = {}) {
		const now = Date.now();
		if (now - this.lastUpdate < 1000) return;

		// Cache kontrolü
		const cacheKey = JSON.stringify(filters);
		const cachedData = this.dataCache.get(cacheKey);
		if (cachedData && (now - cachedData.timestamp) < CONFIG.CACHE_DURATION) {
			this.plannedTable.data = cachedData.data;
			this.updateSummary(cachedData.data);
			uiComponents.renderTableRows('planlanan-tbody', cachedData.data);
			this.updateCompletedToggle();
			return;
		}
		
		try {
			this.showLoading();
			this.lastUpdate = now;
			
			// Timeout ile API çağrısı
			const apiCall = frappe.call({
				method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_production_planning_data',
				args: { filters: JSON.stringify(filters) },
				timeout: CONFIG.DATA_LOAD_TIMEOUT,
				callback: (r) => {
					this.hideLoading();
					
					if (r.exc) {
						this.showError('Veri yüklenirken hata: ' + r.exc);
						return;
					}
					
					const data = r.message;
					
					if (data.error) {
						this.showError(data.error);
						return;
					}
					
					this.plannedTable.data = data.planned || [];
					
					// Cache'e kaydet
					this.dataCache.set(cacheKey, {
						data: this.plannedTable.data,
						timestamp: now
					});
					
					this.updateSummary(data);
					uiComponents.renderTableRows('planlanan-tbody', this.plannedTable.data);
					this.updateCompletedToggle();
				},
				error: (err) => {
					this.hideLoading();
					this.showError('Bağlantı hatası: ' + err);
				}
			});

			// Timeout kontrolü
			// setTimeout(() => {
			// 	if ($('#loading-spinner').is(':visible')) {
			// 		this.hideLoading();
			// 		this.showError('Veri yükleme zaman aşımı. Lütfen tekrar deneyin.');
			// 	}
			// }, CONFIG.DATA_LOAD_TIMEOUT + 1000);
			
		} catch (error) {
			this.hideLoading();
			this.showError('Veriler yüklenirken hata oluştu: ' + error.message);
		}
	}

	// Loading state management - Optimized
	showLoading() {
		uiComponents.setLoading(true);
	}

	hideLoading() {
		uiComponents.setLoading(false);
	}

	// Helper methods for table rendering
	createOptiRowElement(optiGroup) {
		const pvcCount = optiGroup.total_pvc || 0;
		const camCount = optiGroup.total_cam || 0;
		const isCompleted = optiGroup.plan_status === 'Completed';
		const rowClass = utils.getRowClass(pvcCount, camCount, isCompleted);
		const isUrgent = utils.isUrgentDelivery(optiGroup.bitis_tarihi);
		const urgentClass = isUrgent ? 'urgent-delivery' : '';

		const tr = document.createElement('tr');
		tr.className = `${rowClass} ${urgentClass} cursor-pointer`;
		tr.setAttribute('data-opti', optiGroup.opti_no);
		tr.setAttribute('data-id', optiGroup.opti_no);

		tr.innerHTML = `
			<td class="text-center">
				<span class="badge badge-info">${utils.escapeHtml(optiGroup.hafta || '-')}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-primary">${utils.escapeHtml(optiGroup.opti_no || '-')}</span>
			</td>
			<td title="${optiGroup.sales_orders.join(', ')}">
				<span class="font-weight-bold text-primary">${utils.truncateText(optiGroup.sales_orders.join(', '), 20)}</span>
			</td>
			<td title="${optiGroup.bayi_list.join(', ')}">${utils.truncateText(optiGroup.bayi_list.join(', '), 15)}</td>
			<td title="${optiGroup.musteri_list.join(', ')}">${utils.truncateText(optiGroup.musteri_list.join(', '), 25)}</td>
			<td class="text-center">
				<span class="badge badge-warning">${utils.formatDate(optiGroup.siparis_tarihi)}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-danger">${utils.getDeliveryDate(optiGroup.planned_end_date, optiGroup.planlanan_baslangic_tarihi)}</span>
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
				<span class="badge badge-info">${utils.escapeHtml(optiGroup.seri_list.join(', ') || '-')}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-warning">${utils.escapeHtml(optiGroup.renk_list.join(', ') || '-')}</span>
			</td>
		`;

		return tr;
	}

	renderUnplannedTable() {
		const tbody = document.getElementById('planlanmamis-tbody');
		if (!tbody) return;

		if (!this.unplannedTable.data || this.unplannedTable.data.length === 0) {
			tbody.innerHTML = `
				<tr><td colspan="13" class="text-center text-muted">
					<i class="fa fa-info-circle mr-2"></i>Planlanmamış sipariş bulunmuyor
				</td></tr>
			`;
			return;
		}

		// Tüm onaylanmış siparişleri göster
		let filteredData = this.unplannedTable.data;
		
		// Performans için DocumentFragment kullan
		const fragment = document.createDocumentFragment();
		
		filteredData.forEach((item, index) => {
			const row = this.createUnplannedRowElement(item);
			fragment.appendChild(row);
		});
		
		tbody.innerHTML = '';
		tbody.appendChild(fragment);
		// Event binding sadece bindEvents()'da yapılıyor - duplicate önlemek için
		this.bindTableEvents();
	}

	createUnplannedRowElement(item) {
		const row = document.createElement('tr');
		
		// PVC/Cam renk kodlaması - Planlanan tablosuyla aynı
		const pvcCount = parseFloat(item.pvc_count || 0);
		const camCount = parseFloat(item.cam_count || 0);
		const isCompleted = false; // Planlanmamış siparişler hiçbir zaman tamamlanmış değil
		const rowClass = utils.getRowClass(pvcCount, camCount, isCompleted);
		
		// DEBUG logları performans için kaldırıldı
		
		// Acil durum kontrolü
		const isUrgent = item.acil == 1;
		const urgentClass = isUrgent ? 'urgent-delivery' : '';
		
		// İş akışı durumu badge'i
		const workflowState = item.is_akisi_durumu || item.workflow_state || 'Bilinmiyor';
		let statusBadge;
		
		switch(workflowState) {
			case 'Onaylandı':
				statusBadge = { label: 'Onaylandı', bg: '#28a745', color: '#fff' };
				break;
			case 'Yeni Sipariş':
				statusBadge = { label: 'Yeni Sipariş', bg: '#17a2b8', color: '#fff' };
				break;
			case 'Muhasebe Onay Bekleniyor':
				statusBadge = { label: 'Muhasebe Onay Bekleniyor', bg: '#ffc107', color: '#000' };
				break;
			default:
				statusBadge = { label: workflowState, bg: '#6c757d', color: '#fff' };
		}
		
		// Veri hazırlama - hover için tam metinler
		const bayiText = item.bayi || '-';
		const truncatedBayi = utils.truncateText(bayiText, 15);
		
		const musteriText = item.musteri || '-';
		const truncatedMusteri = utils.truncateText(musteriText, 20);
		
		const seriText = item.seri || '-';
		const truncatedSeri = utils.truncateText(seriText, 15);
		
		const renkText = item.renk || '-';
		const truncatedRenk = utils.truncateText(renkText, 15);
		
		const aciklamaText = item.aciklama || '-';
		const truncatedAciklama = utils.truncateText(aciklamaText, 40);

		// Row class'ını ayarla
		row.className = `${rowClass} ${urgentClass} cursor-pointer`;
		row.dataset.id = item.sales_order || '';

		row.innerHTML = `
			<td title="${utils.escapeHtml(item.sales_order || '-')}">
				<span class="font-weight-bold text-primary">${utils.escapeHtml(item.sales_order || '-')}</span>
			</td>
			<td title="${utils.escapeHtml(bayiText)}">
				<span class="text-truncate">${utils.escapeHtml(truncatedBayi)}</span>
			</td>
			<td title="${utils.escapeHtml(musteriText)}">
				<span class="text-truncate">${utils.escapeHtml(truncatedMusteri)}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-warning">${utils.formatDate(item.siparis_tarihi)}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-danger">${utils.formatDate(item.bitis_tarihi)}</span>
			</td>
			<td class="text-center">
				<span class="badge" style="background-color: ${statusBadge.bg}; color: ${statusBadge.color};">${statusBadge.label}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-danger">${utils.escapeHtml(item.pvc_count || '0')}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-primary">${utils.escapeHtml(item.cam_count || '0')}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-success">${utils.escapeHtml(item.total_mtul ? item.total_mtul.toFixed(2) : '0.00')}</span>
			</td>
			<td class="text-center" title="${utils.escapeHtml(seriText)}">
				<span class="badge badge-info">${utils.escapeHtml(truncatedSeri)}</span>
			</td>
			<td class="text-center" title="${utils.escapeHtml(renkText)}">
				<span class="badge badge-warning">${utils.escapeHtml(truncatedRenk)}</span>
			</td>
			<td title="${utils.escapeHtml(aciklamaText)}" style="min-width: 200px;">
				<span class="text-truncate">${utils.escapeHtml(truncatedAciklama)}</span>
			</td>
			<td class="text-center">
				${isUrgent ? '<span class="badge badge-danger"><i class="fa fa-exclamation-triangle"></i> ACİL</span>' : '<span class="badge badge-secondary">-</span>'}
			</td>
		`;
		
		return row;
	}

	// Independent summary update methods
	updatePlannedSummary() {
		// Opti numarasına göre gruplandır
		const optiGroups = {};
		this.plannedTable.data.forEach(order => {
			const optiNo = order.opti_no;
			if (!optiGroups[optiNo]) {
				optiGroups[optiNo] = {
					opti_no: optiNo,
					plan_status: order.plan_status
				};
			}
		});
		
		const totalCount = Object.keys(optiGroups).length;
		const completedCount = Object.values(optiGroups).filter(opti => opti.plan_status === 'Completed').length;
		
		// Update table count
		const element = document.getElementById('planlanan-count');
		if (element) element.textContent = totalCount;
		
		// Update summary card
		const summaryElement = document.getElementById('planlanan-sayisi');
		if (summaryElement) summaryElement.textContent = totalCount;
		
		// Update completed toggle count
		const toggleBtn = document.getElementById('toggle-completed-btn');
		if (toggleBtn) {
			const icon = this.plannedTable.showCompleted ? 'fa-eye' : 'fa-eye-slash';
			const text = this.plannedTable.showCompleted ? 'Tamamlananları Gizle' : 'Tamamlananları Göster';
			toggleBtn.innerHTML = `<i class="fa ${icon} mr-1"></i>${text} (${completedCount}/${totalCount})`;
		}
		
		// Update total count
		this.updateTotalSummary();
	}

	updateTotalSummary() {
		// Planlanan sayısını al
		const planlananCount = this.plannedTable.data ? Object.keys(
			this.plannedTable.data.reduce((groups, order) => {
				groups[order.opti_no] = true;
				return groups;
			}, {})
		).length : 0;
		
		// Planlanmamış sayısını al
		const planlanmamisCount = this.unplannedTable.data ? this.unplannedTable.data.length : 0;
		
		// Toplam sayıyı hesapla
		const totalCount = planlananCount + planlanmamisCount;
		
		// Update summary card
		const summaryElement = document.getElementById('toplam-sayisi');
		if (summaryElement) summaryElement.textContent = totalCount;
	}

	updateUnplannedSummary() {
		const count = this.unplannedTable.data.length;
		
		// Update table count
		const element = document.getElementById('planlanmamis-count');
		if (element) element.textContent = count;
		
		// Update summary card
		const summaryElement = document.getElementById('planlanmamis-sayisi');
		if (summaryElement) summaryElement.textContent = count;
		
		// Update total count
		this.updateTotalSummary();
	}

	// Update summary cards - Kaldırıldı
	updateSummary(data) {
		// updateSummary fonksiyonu kaldırıldı - özet kartlar artık kullanılmıyor
		console.log('updateSummary kaldırıldı - özet kartlar güncellenmeyecek');
	}

	updateCompletedToggle() {
		const completedCountElement = document.getElementById('completedCount');
		if (completedCountElement && this.plannedTable.data) {
			// Opti numarasına göre gruplandır ve tamamlanan üretim planı sayısını hesapla
			const optiGroups = {};
			this.plannedTable.data.forEach(order => {
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

	renderTableRows(tbodyId, rows) {
		const tbody = document.getElementById(tbodyId);
		if (!tbody) return;

		if (!rows || rows.length === 0) {
			tbody.innerHTML = `
				<tr><td colspan="13" class="text-center text-muted">
					<i class="fa fa-info-circle mr-2"></i>Henüz planlama bulunmuyor
				</td></tr>
			`;
			return;
		}
		
		// Filtreleri al
		const filters = this.getPlanlananFilters();
		
		// Tamamlananları göster/gizle filtresi
		let filteredData = rows;
		if (!filters.showCompleted) {
			filteredData = rows.filter(item => item.plan_status !== 'Completed');
		}
		
		// Performans için sadece ilk 200 kayıt
		if (filteredData.length > 200) {
			filteredData = filteredData.slice(0, 200);
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
					planned_end_date: order.planned_end_date,
					seri: order.seri,
					renk: order.renk,
					plan_status: order.plan_status,
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
			if (order.bayi) optiGroups[optiNo].bayi_list.add(order.bayi);
			if (order.musteri) optiGroups[optiNo].musteri_list.add(order.musteri);
			if (order.seri) optiGroups[optiNo].seri_list.add(order.seri);
			if (order.renk) optiGroups[optiNo].renk_list.add(order.renk);
		});
		
		// Set'leri Array'e çevir
		Object.values(optiGroups).forEach(group => {
			group.bayi_list = Array.from(group.bayi_list);
			group.musteri_list = Array.from(group.musteri_list);
			group.seri_list = Array.from(group.seri_list);
			group.renk_list = Array.from(group.renk_list);
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
			const optiRow = this.createOptiRowElement(optiGroup);
			fragment.appendChild(optiRow);
		});
		
		tbody.innerHTML = '';
		tbody.appendChild(fragment);
		this.bindTableEvents();
	}

	createOptiRowElement(optiGroup) {
		const row = document.createElement('tr');
		const pvcCount = optiGroup.total_pvc || 0;
		const camCount = optiGroup.total_cam || 0;
		const isCompleted = optiGroup.plan_status === 'Completed';
		const rowClass = utils.getRowClass(pvcCount, camCount, isCompleted);
		const isUrgent = utils.isUrgentDelivery(optiGroup.bitis_tarihi);
		const urgentClass = isUrgent ? 'urgent-delivery' : '';
		
		// Doğru sınıf ataması - getRowClass içinde completed kontrolü var
		row.className = `${rowClass} ${urgentClass} opti-row cursor-pointer`;
		row.dataset.opti = optiGroup.opti_no;
		
		// Çoklu sipariş verilerini birleştir - hover için
		const siparisText = optiGroup.sales_orders.join(', ');
		const truncatedSiparis = utils.truncateText(siparisText, 20);
		
		// Bayi verilerini birleştir - hover için tüm benzersiz bayileri göster
		let bayiText = optiGroup.bayi || '-';
		if (optiGroup.bayi_list && optiGroup.bayi_list.length > 0) {
			bayiText = optiGroup.bayi_list.join(', ');
		}
		const truncatedBayi = utils.truncateText(bayiText, 15);
		
		// Müşteri verilerini birleştir - hover için tüm benzersiz müşterileri göster
		let musteriText = optiGroup.musteri || '-';
		if (optiGroup.musteri_list && optiGroup.musteri_list.length > 0) {
			musteriText = optiGroup.musteri_list.join(', ');
		}
		const truncatedMusteri = utils.truncateText(musteriText, 25);
		
		// Seri verilerini birleştir - hover için tüm benzersiz serileri göster
		let seriText = optiGroup.seri || '-';
		if (optiGroup.seri_list && optiGroup.seri_list.length > 0) {
			seriText = optiGroup.seri_list.join(', ');
		}
		const truncatedSeri = utils.truncateText(seriText, 15);
		
		// Renk verilerini birleştir - hover için tüm benzersiz renkleri göster
		let renkText = optiGroup.renk || '-';
		if (optiGroup.renk_list && optiGroup.renk_list.length > 0) {
			renkText = optiGroup.renk_list.join(', ');
		}
		const truncatedRenk = utils.truncateText(renkText, 15);
		
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
			<td title="${bayiText}">
				<span class="text-truncate">${truncatedBayi}</span>
			</td>
			<td title="${musteriText}">
				<span class="text-truncate">${truncatedMusteri}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-warning">${utils.formatDate(optiGroup.siparis_tarihi)}</span>
			</td>
			<td class="text-center">
				<span class="badge badge-danger">${utils.getDeliveryDate(optiGroup.planned_end_date, optiGroup.planlanan_baslangic_tarihi)}</span>
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
				<span class="badge badge-warning">${utils.formatDate(optiGroup.planlanan_baslangic_tarihi)}</span>
			</td>
			<td class="text-center" title="${seriText}">
				<span class="badge badge-info">${truncatedSeri}</span>
			</td>
			<td class="text-center" title="${renkText}">
				<span class="badge badge-warning">${truncatedRenk}</span>
			</td>
		`;
		
		return row;
	}

	bindTableEvents() {
		// Use event delegation for better performance
		const tbody = document.getElementById('planlanan-tbody');
		if (!tbody) return;
		
		utils.delegate(tbody, 'tr[data-opti]', 'click', (e, target) => {
			if (!e.target.closest('button') && !e.target.closest('a')) {
				this.showOptiDetails(target.dataset.opti);
			}
		});
		

	}

	startAutoRefresh() {
		// Önceki interval'ı temizle
		if (this.updateInterval) {
			clearInterval(this.updateInterval);
		}
		
		// 10 dakikada bir auto refresh - sadece sayfa aktif ve modal açık değilse
		this.updateInterval = setInterval(() => {
			if (!document.hidden && !document.querySelector('.modal.show')) {
				// Sadece planlanan verileri yenile (planlanmamış veriler daha az değişir)
				this.loadPlannedData().catch(error => {
					console.warn('Auto refresh hatası (planlanan):', error);
				});
			}
		}, 600000); // 10 dakika (600 saniye)
	}

	// Enhanced error handling
	showError(message, title = 'Hata') {
		errorHandler.log(new Error(message), this.errorContext);
		
		// Toast notification
		frappe.show_alert({
			message: message,
			indicator: 'red'
		}, 5);
		
		// Detailed error modal for critical errors
		if (message.includes('API') || message.includes('network')) {
			const modal = modalManager.createModal('error-modal', title, 'modal-md');
			if (modal) {
				modal.find('.modal-content-inner').html(`
					<div class="alert alert-danger">
						<i class="fa fa-exclamation-circle mr-2"></i>
						<strong>Hata Detayı:</strong><br>
						${message}
					</div>
					<div class="mt-3">
						<button class="btn btn-primary" onclick="location.reload()">
							<i class="fa fa-refresh mr-2"></i>Sayfayı Yenile
						</button>
						<button class="btn btn-secondary ml-2" onclick="modalManager.clearCache()">
							<i class="fa fa-trash mr-2"></i>Cache Temizle
						</button>
					</div>
				`);
			}
		}
	}

	showSuccess(message) {
		frappe.show_alert({
			message: message,
			indicator: 'green'
		}, 3);
	}

	// Performance monitoring
	measurePerformance(name, fn) {
		return errorHandler.measureTime(name, fn);
	}

	// Cache management
	clearCache() {
		this.dataCache.clear();
		modalManager.clearCache();
		this.lastCacheUpdate = 0;
		state.setPlannedData([]);
		state.setUnplannedData([]);
		this.showSuccess('Cache temizlendi');
	}

	destroy() {
		// Clear all timers - Enhanced cleanup
		if (this.refreshTimer) {
			clearInterval(this.refreshTimer);
		}
		if (this.updateInterval) {
			clearInterval(this.updateInterval);
		}
		if (this.debounceTimer) {
			clearTimeout(this.debounceTimer);
		}

		// Clear table event handlers
		const plannedTbody = document.getElementById('planlanan-tbody');
		if (plannedTbody && this.plannedTableClickHandler) {
			plannedTbody.removeEventListener('click', this.plannedTableClickHandler);
		}
		
		const unplannedTbody = document.getElementById('planlanmamis-tbody');
		if (unplannedTbody && this.unplannedTableClickHandler) {
			unplannedTbody.removeEventListener('click', this.unplannedTableClickHandler);
		}
		
		// Clear event listeners
		this.eventListeners.forEach((listener, element) => {
			element.removeEventListener(listener.type, listener.handler);
		});
		this.eventListeners.clear();
		
		// Clear virtual scrollers
		if (this.plannedVirtualScroller) {
			this.plannedVirtualScroller.destroy();
		}
		if (this.unplannedVirtualScroller) {
			this.unplannedVirtualScroller.destroy();
		}
		
		// Clear modal references
		this.clearModalReferences();
		
		// Clear data caches
		this.dataCache.clear();
		this.plannedTable.data = [];
		this.unplannedTable.data = [];
		
		// Force garbage collection hint
		if (window.gc) {
			window.gc();
		}
	}
	
	clearModalReferences() {
		// Tüm modal referanslarını temizle
		const modals = document.querySelectorAll('.modal');
		modals.forEach(modal => {
			if (modal.id && modal.id.startsWith('order-details-')) {
				modal.remove();
			}
		});
	}
}

// Global instance - Enhanced with cleanup
let appInstance = null;

// Global functions for backward compatibility
window.loadProductionData = () => {
	if (appInstance) {
		appInstance.loadProductionData();
	}
};

window.toggleCompletedItems = () => {
	if (appInstance) {
		showCompletedItems = !showCompletedItems;
		appInstance.loadProductionData();
	}
};

// Work Orders Modal - STABLE VERSION
window.showWorkOrdersPaneli = function(salesOrderId, productionPlan = null) {
	if (!salesOrderId) {
		frappe.show_alert({
			message: 'Geçersiz sipariş numarası',
			indicator: 'red'
		});
		return;
	}

	// Modal ID unique yap
	const modalId = 'work-orders-modal-' + salesOrderId.replace(/[^a-zA-Z0-9]/g, '');
	
	// Önceki modal varsa kapat
	if ($('#' + modalId).length) {
		$('#' + modalId).modal('hide').remove();
	}
	
	// Modal HTML - Bootstrap standart
	const modal = new frappe.ui.Dialog({
		title: `<i class="fa fa-list mr-2"></i>İş Emirleri - ${salesOrderId}`,
		size: 'extra-large',
		fields: [{
			fieldtype: 'HTML',
			fieldname: 'work_orders_content',
			options: `
				<div id="work-orders-loading" class="text-center p-4">
					<div class="spinner-border text-primary" role="status">
						<span class="sr-only">Yükleniyor...</span>
					</div>
					<p class="mt-3">İş emirleri yükleniyor...</p>
				</div>
			`
		}],
		primary_action_label: 'Kapat',
		primary_action: function() {
			modal.hide();
		}
	});

	// Modal header sarı yap
	modal.$wrapper.find('.modal-header').css({
		'background-color': '#ffc107',
		'color': '#333'
	});

	modal.show();

	// API çağrısı
	frappe.call({
		method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_work_orders_for_sales_order',
		args: { 
			sales_order: salesOrderId,
			production_plan: productionPlan 
		},
		timeout: 30000, // 30 saniye timeout
		callback: function(r) {
			const contentDiv = modal.fields_dict.work_orders_content.$wrapper;
			
			if (r.exc) {
				contentDiv.html(`
					<div class="alert alert-danger">
						<i class="fa fa-exclamation-triangle mr-2"></i>
						Hata: ${r.exc}
					</div>
				`);
				return;
			}

			if (!r.message || r.message.length === 0) {
				contentDiv.html(`
					<div class="alert alert-info">
						<i class="fa fa-info-circle mr-2"></i>
						Bu sipariş için iş emri bulunamadı.
					</div>
				`);
				return;
			}

			// Tarih formatla fonksiyonu
			const formatDateTime = (dateTime) => {
				if (!dateTime) return '-';
				try {
					return new Date(dateTime).toLocaleString('tr-TR', {
						day: '2-digit', month: '2-digit', year: 'numeric',
						hour: '2-digit', minute: '2-digit'
					});
				} catch (e) {
					return dateTime;
				}
			};

			// İş emirleri accordion şeklinde
			let html = `
				<div class="accordion" id="workOrdersAccordion">
			`;

			r.message.forEach((wo, index) => {
				const statusClass = wo.status === 'Completed' ? 'badge-success' : 'badge-warning';
				const statusText = wo.status === 'Completed' ? 'Tamamlandı' : 'Devam Ediyor';
				const accordionId = `wo-${index}`;
				
				html += `
					<div class="card mb-2">
						<div class="card-header" id="heading-${accordionId}" style="background-color: #f8f9fa; cursor: pointer;"
							 onclick="toggleWorkOrderAccordion('${accordionId}', '${wo.name}', ${index})">
							<div class="d-flex justify-content-between align-items-center">
								<div class="d-flex align-items-center">
									<i class="fa fa-chevron-down mr-2" id="icon-${accordionId}"></i>
									<strong>${wo.name}</strong>
									<span class="badge ${statusClass} ml-2">${statusText}</span>
								</div>
								<div class="text-muted">
									<small>Miktar: ${wo.qty || 0} | Üretilen: ${wo.produced_qty || 0}</small>
								</div>
							</div>
						</div>
						<div class="collapse" id="collapse-${accordionId}">
							<div class="card-body">
								<div class="row mb-3">
									<div class="col-md-6">
										<strong>Plan Başlangıç:</strong> ${formatDateTime(wo.planned_start_date) || '-'}
									</div>
									<div class="col-md-6">
										<strong>Plan Bitiş:</strong> ${formatDateTime(wo.planned_end_date) || '-'}
									</div>
								</div>
								<div id="operations-container-${accordionId}">
									<div class="text-center p-2">
										<small class="text-muted">Operasyonlar yükleniyor...</small>
									</div>
								</div>
							</div>
						</div>
					</div>
				`;
			});

			html += `</div>`;

			contentDiv.html(html);
		},
		error: function(err) {
			const contentDiv = modal.fields_dict.work_orders_content.$wrapper;
			contentDiv.html(`
				<div class="alert alert-danger">
					<i class="fa fa-exclamation-triangle mr-2"></i>
					Bağlantı hatası: ${err.message || 'Bilinmeyen hata'}
				</div>
			`);
		}
	});
};

// Yeni accordion toggle fonksiyonu - GLOBAL
window.toggleWorkOrderAccordion = function(accordionId, woName, index) {
	const collapseElement = $(`#collapse-${accordionId}`);
	const icon = $(`#icon-${accordionId}`);
	const operationsContainer = $(`#operations-container-${accordionId}`);
	
	// Bootstrap collapse toggle
	collapseElement.collapse('toggle');
	
	// Mevcut durumu kontrol et
	const isCurrentlyOpen = collapseElement.hasClass('show');
	
	// Icon değiştir ve operasyonları yükle
	if (!isCurrentlyOpen) {
		// Açılıyor - operasyonları yükle
		icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
		
		// Operasyonları yükle
		operationsContainer.show();
		operationsContainer.html('<div class="text-center p-2"><small>Operasyonlar yükleniyor...</small></div>');
		
		frappe.call({
			method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_work_order_operations',
			args: { work_order: woName },
			timeout: 30000, // 30 saniye timeout
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					let opsHtml = `
						<div class="mt-3">
							<h6 class="text-primary mb-2">
								<i class="fa fa-cogs mr-1"></i>Operasyonlar
							</h6>
							<div class="table-responsive">
								<table class="table table-sm table-bordered" style="margin: 0; background: white;">
									<thead>
										<tr style="background: #e9ecef; color: #333;">
											<th style="padding: 8px; font-weight: 600;">Operasyon</th>
											<th style="padding: 8px; font-weight: 600;">Durum</th>
											<th style="padding: 8px; font-weight: 600;">Tamamlanan</th>
											<th style="padding: 8px; font-weight: 600;">Planlanan Başlangıç</th>
											<th style="padding: 8px; font-weight: 600;">Planlanan Bitiş</th>
											<th style="padding: 8px; font-weight: 600;">Fiili Başlangıç</th>
											<th style="padding: 8px; font-weight: 600;">Fiili Bitiş</th>
										</tr>
									</thead>
									<tbody style="background: white;">
					`;
					
					r.message.forEach(op => {
						const opStatus = op.status === 'Completed' ? 
							'<span class="badge badge-success badge-sm">Tamamlandı</span>' :
							'<span class="badge badge-warning badge-sm">Bekliyor</span>';
						
						// Tarih formatla
						const formatDateTime = (dateTime) => {
							if (!dateTime) return '-';
							try {
								return new Date(dateTime).toLocaleString('tr-TR', {
									day: '2-digit', month: '2-digit', year: 'numeric',
									hour: '2-digit', minute: '2-digit'
								});
							} catch (e) {
								return dateTime;
							}
						};
						
						opsHtml += `
							<tr style="background: white;">
								<td style="padding: 8px; color: #333;">${op.operation || '-'}</td>
								<td style="padding: 8px;">${opStatus}</td>
								<td style="padding: 8px; text-align: center; color: #333;">${op.completed_qty || 0}</td>
								<td style="padding: 8px; color: #333;">${formatDateTime(op.planned_start_time)}</td>
								<td style="padding: 8px; color: #333;">${formatDateTime(op.planned_end_time)}</td>
								<td style="padding: 8px; color: #333;">${formatDateTime(op.actual_start_time)}</td>
								<td style="padding: 8px; color: #333;">${formatDateTime(op.actual_end_time)}</td>
							</tr>
						`;
					});
					
					opsHtml += '</tbody></table></div></div>';
					operationsContainer.html(opsHtml);
				} else {
					operationsContainer.html('<div class="text-muted p-2"><small>Operasyon bulunamadı</small></div>');
				}
			},
			error: function() {
				operationsContainer.html('<div class="text-danger p-2"><small>Operasyonlar yüklenemedi</small></div>');
			}
		});
	} else {
		icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
		operationsContainer.hide();
	}
};

// Eski fonksiyon - geriye uyumluluk için
window.toggleWorkOrderOperations = function(woName, index) {
	// Eski fonksiyon artık kullanılmıyor, yeni accordion fonksiyonunu çağır
	window.toggleWorkOrderAccordion(`wo-${index}`, woName, index);
};

// LEGACY - Bu fonksiyon artık kullanılmıyor
// İş Emirleri Modal Content - 2. ekran formatı  
function updateWorkOrdersModalContent_LEGACY(contentDiv, data, salesOrderId) {
	if (!data || !Array.isArray(data) || data.length === 0) {
		contentDiv.html(`
			<div class="alert alert-warning m-3">
				<i class="fa fa-info-circle mr-2"></i>Bu sipariş için iş emri bulunamadı.
			</div>
		`);
		return;
	}

	// 2. ekrandaki format - basit ve temiz
	let html = `
		<div class="row mb-3">
			<div class="col-12">
				<div class="d-flex align-items-center">
					<i class="fa fa-list mr-2"></i>
					<span><strong>İş Emirleri Detayları</strong></span>
				</div>
				<div class="mt-2">
					<small>Sipariş No: <strong>${salesOrderId}</strong></small>
				</div>
			</div>
		</div>

		<div class="table-responsive">
			<table class="table table-sm" style="background: white;">
				<thead style="background: #6c757d; color: white;">
					<tr>
						<th style="padding: 8px;">İş Emri</th>
						<th style="padding: 8px;">Durum</th>
						<th style="padding: 8px;">Miktar</th>
						<th style="padding: 8px;">Üretilen</th>
						<th style="padding: 8px;">Planlanan Başlangıç</th>
						<th style="padding: 8px;">Planlanan Bitiş</th>
					</tr>
				</thead>
				<tbody style="background: white;">
	`;

	data.forEach((wo, index) => {
		const statusBadge = wo.status === 'Completed' ? 'badge-success' : 
						   wo.status === 'In Progress' ? 'badge-warning' : 
						   wo.status === 'Not Started' ? 'badge-secondary' : 'badge-info';
		
		const statusText = wo.status === 'Completed' ? 'Tamamlandı' :
						  wo.status === 'In Progress' ? 'Devam Ediyor' :
						  wo.status === 'Not Started' ? 'Başlamadı' : wo.status;

		// Durum badge'i - Tamamlandı yeşil olsun
		const durumBadgeStyle = wo.status === 'Completed' ? 
			'background: #28a745; color: white;' :
			wo.status === 'Not Started' ? 
			'background: #ffc107; color: #333;' : 
			'background: #6c757d; color: white;';
		
		html += `
			<tr style="background: white; cursor: pointer;" class="work-order-row" data-work-order="${wo.name}" data-index="${index}">
				<td style="padding: 8px;">
					<i class="fa fa-chevron-down toggle-operations mr-2" style="color: #007bff; cursor: pointer;"></i>
					<strong style="color: #333;">${wo.name || '-'}</strong>
				</td>
				<td style="padding: 8px;">
					<span class="badge" style="${durumBadgeStyle}">${statusText}</span>
				</td>
				<td style="padding: 8px;">
					<span style="color: #333;">${wo.qty || '0'}</span>
				</td>
				<td style="padding: 8px;">
					<span style="color: #333;">${wo.produced_qty || '0'}</span>
				</td>
				<td style="padding: 8px;">
					<span style="color: #333;">${utils.formatDate(wo.planned_start_date) || '-'}</span>
				</td>
				<td style="padding: 8px;">
					<span style="color: #333;">${utils.formatDate(wo.planned_end_date) || '-'}</span>
				</td>
			</tr>
			<tr id="operations-row-${index}" style="display: none; background: white;">
				<td colspan="6" style="padding: 15px;">
					<div class="operations-container" style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
						<div class="text-center">
							<div class="spinner-border spinner-border-sm text-primary" role="status">
								<span class="sr-only">Yükleniyor...</span>
							</div>
							<span class="ml-2">Operasyonlar yükleniyor...</span>
						</div>
					</div>
				</td>
			</tr>
		`;
	});

	html += `
				</tbody>
			</table>
		</div>
	`;

	contentDiv.html(html);

	// Event listener'ları ekle - açılır/kapanır özellik
	contentDiv.find('.toggle-operations').on('click', function(e) {
		e.preventDefault();
		e.stopPropagation();
		
		const row = $(this).closest('tr');
		const workOrderName = row.data('work-order');
		const index = row.data('index');
		const operationsRow = $(`#operations-row-${index}`);
		const icon = $(this);
		
		if (operationsRow.is(':visible')) {
			// Kapat
			operationsRow.hide();
			icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
		} else {
			// Aç ve operasyonları yükle
			operationsRow.show();
			icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
			loadOperationsForWorkOrder(workOrderName, index);
		}
	});
}

// Operasyon yükleme fonksiyonu
function loadOperationsForWorkOrder(workOrderName, index) {
	const operationsContainer = $(`.operations-container`).eq(index);
	if (!operationsContainer.length) return;
	
	frappe.call({
		method: 'uretim_planlama.uretim_planlama.page.uretim_planlama_paneli.uretim_planlama_paneli.get_work_order_operations',
		args: { work_order: workOrderName },
		timeout: 30000, // 30 saniye timeout
		callback: (r) => {
			if (r.exc) {
				operationsContainer.html(`
					<div class="alert alert-danger">
						<i class="fa fa-exclamation-triangle mr-2"></i>
						Operasyonlar yüklenemedi: ${r.exc}
					</div>
				`);
				return;
			}
			
			if (!r.message || !Array.isArray(r.message) || r.message.length === 0) {
				operationsContainer.html(`
					<div class="alert alert-warning">
						<i class="fa fa-info-circle mr-2"></i>
						Bu iş emri için operasyon bulunamadı
					</div>
				`);
				return;
			}
			
			renderOperationsTable(operationsContainer, r.message);
		},
		error: (err) => {
			operationsContainer.html(`
				<div class="alert alert-danger">
					<i class="fa fa-exclamation-triangle mr-2"></i>
					Bağlantı hatası: ${err}
				</div>
			`);
		}
	});
}

// Operasyon tablosu render fonksiyonu
function renderOperationsTable(container, operations) {
	let html = `
		<div class="operations-header mb-3">
			<h6 class="mb-2" style="color: #333;">
				<i class="fa fa-cogs mr-2"></i>Operasyonlar (${operations.length})
			</h6>
		</div>
		<div class="table-responsive">
			<table class="table table-sm table-bordered" style="background: white;">
				<thead style="background: #6c757d; color: white;">
					<tr>
						<th style="padding: 6px;">Operasyon</th>
						<th style="padding: 6px;">Durum</th>
						<th style="padding: 6px;">Miktar</th>
						<th style="padding: 6px;">Planlanan Başlangıç</th>
						<th style="padding: 6px;">Planlanan Bitiş</th>
						<th style="padding: 6px;">Fiili Başlangıç</th>
						<th style="padding: 6px;">Fiili Bitiş</th>
					</tr>
				</thead>
				<tbody style="background: white;">
	`;
	
	operations.forEach(op => {
		let statusText = op.status || 'Pending';
		if (statusText === 'Completed') statusText = 'Tamamlandı';
		else if (statusText === 'In Progress') statusText = 'Devam Ediyor';
		else if (statusText === 'Not Started') statusText = 'Başlamadı';
		else statusText = 'Bekliyor';
		
		const statusStyle = op.status === 'Completed' ? 'background: #28a745; color: white;' : 
						   op.status === 'In Progress' ? 'background: #ffc107; color: #333;' : 
						   'background: #6c757d; color: white;';
		
		html += `
			<tr style="background: white;">
				<td style="padding: 6px;"><strong style="color: #333;">${op.operation || '-'}</strong></td>
				<td style="padding: 6px;"><span class="badge" style="${statusStyle}">${statusText}</span></td>
				<td style="padding: 6px;"><span style="color: #333;">${op.completed_qty || '0'}</span></td>
				<td style="padding: 6px;"><span style="color: #333;">${utils.formatDate(op.planned_start_time) || '-'}</span></td>
				<td style="padding: 6px;"><span style="color: #333;">${utils.formatDate(op.planned_end_time) || '-'}</span></td>
				<td style="padding: 6px;"><span style="color: #333;">${utils.formatDate(op.actual_start_time) || '-'}</span></td>
				<td style="padding: 6px;"><span style="color: #333;">${utils.formatDate(op.actual_end_time) || '-'}</span></td>
			</tr>
		`;
	});
	
	html += `
				</tbody>
			</table>
		</div>
	`;
	
	container.html(html);
}



// Cleanup on page unload
window.addEventListener('beforeunload', () => {
	if (appInstance) {
		appInstance.destroy();
		appInstance = null;
	}
});

// Page initialization
frappe.pages['uretim_planlama_paneli'].on_page_load = function(wrapper) {
	try {
		if (appInstance) {
			appInstance.destroy();
			appInstance = null;
		}
		
		// Create page instance with wrapper - single column for full width
		const page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Üretim Planlama Paneli',
			single_column: true  // Bu çok önemli - tam genişlik için
		});
		
		appInstance = new UretimPlanlamaPaneli(page);
		
	} catch (error) {
		console.error('Sayfa yüklenirken kritik hata oluştu:', error);
		frappe.msgprint('Sayfa yüklenirken kritik hata oluştu: ' + error.message);
	}
}; 

// Modal helper functions
function updateOptiDetailsModal(data) {
	const modal = $('.modal:visible');
	if (!modal.length) return;
	
	const content = modal.find('#opti-details-content');
	if (!content.length) return;
	
	let html = `
		<div class="alert alert-info">
			<i class="fa fa-info-circle mr-2"></i>
			<strong>Opti ${data.opti_no}</strong> - Toplam ${data.orders.length} sipariş planlandı
		</div>
		
		<div class="row mb-3">
			<div class="col-12 text-center">
				<a href="/app/production-plan/${data.production_plan}" target="_blank" class="btn btn-primary btn-lg">
					<i class="fa fa-cogs mr-2"></i>Üretim Planını Görüntüle
				</a>
			</div>
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
								<th>İşlemler</th>
							</tr>
						</thead>
						<tbody>
	`;

	data.orders.forEach(order => {
		const orderDate = utils.formatDate(order.siparis_tarihi);
		
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
						<a href="/app/sales-order/${order.sales_order}" target="_blank" class="btn btn-sm btn-outline-primary mb-1">
							<i class="fa fa-external-link mr-1"></i>Sipariş
						</a>
						<button class="btn btn-sm btn-outline-success" onclick="window.showWorkOrdersPaneli('${order.sales_order}', '${data.production_plan}')">
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
</div>`;
	
	content.html(html);
}









function updateOrderDetailsModal(data) {
	const modal = $('.modal:visible');
	if (!modal.length) return;
	
	// order-details-content-{salesOrderId} formatında ID'yi bul
	const content = modal.find('[id^="order-details-content-"]');
	if (!content.length) return;
	
	let html = `
		<div class="alert alert-info">
			<i class="fa fa-info-circle mr-2"></i>
			<strong>Sipariş ${data.sales_order}</strong> - Detaylı Bilgiler
		</div>
		
		<div class="row">
			<div class="col-md-6">
				<div class="card">
					<div class="card-header" style="background: #17a2b8; color: white; border: none;">
						<i class="fa fa-shopping-cart mr-2"></i>Sipariş Bilgileri
					</div>
					<div class="card-body">
						<table class="table table-sm table-bordered">
							<tr>
								<td><strong>Sipariş No:</strong></td>
								<td><span class="badge badge-primary">${data.sales_order || '-'}</span></td>
							</tr>
							<tr>
								<td><strong>Bayi:</strong></td>
								<td>${data.bayi || '-'}</td>
							</tr>
							<tr>
								<td><strong>Müşteri:</strong></td>
								<td>${data.musteri || '-'}</td>
							</tr>
							<tr>
								<td><strong>Sipariş Tarihi:</strong></td>
								<td>${utils.formatDate(data.siparis_tarihi)}</td>
							</tr>
							<tr>
								<td><strong>Teslim Tarihi:</strong></td>
								<td>${utils.formatDate(data.bitis_tarihi)}</td>
							</tr>
						</table>
					</div>
				</div>
			</div>
			<div class="col-md-6">
				<div class="card">
					<div class="card-header bg-success text-white">
						<i class="fa fa-cogs mr-2"></i>Ürün Bilgileri
					</div>
					<div class="card-body">
						<table class="table table-sm table-bordered">
							<tr>
								<td><strong>Seri:</strong></td>
								<td>
									${data.seri_list && data.seri_list.length > 0 ? 
										data.seri_list.map(seri => `<span class="badge badge-info mr-1">${seri}</span>`).join('') : 
										`<span class="badge badge-info">${data.seri || '-'}</span>`
									}
								</td>
							</tr>
							<tr>
								<td><strong>Renk:</strong></td>
								<td>
									${data.renk_list && data.renk_list.length > 0 ? 
										data.renk_list.map(renk => `<span class="badge badge-warning mr-1">${renk}</span>`).join('') : 
										`<span class="badge badge-warning">${data.renk || '-'}</span>`
									}
								</td>
							</tr>
							<tr>
								<td><strong>PVC:</strong></td>
								<td>
									<span class="badge badge-danger mr-2">ADET: ${data.pvc_qty || '0'}</span>
									<span class="badge badge-warning">MTÜL: ${data.pvc_qty && data.total_mtul ? 
										((parseFloat(data.pvc_qty) / (parseFloat(data.pvc_qty) + parseFloat(data.cam_qty || 0))) * parseFloat(data.total_mtul)).toFixed(2) : '0.00'}</span>
								</td>
							</tr>
							<tr>
								<td><strong>CAM:</strong></td>
								<td>
									<span class="badge badge-primary mr-2">ADET: ${data.cam_qty || '0'}</span>
									<span class="badge badge-info">M2: ${data.cam_qty ? (parseFloat(data.cam_qty) * 0.95).toFixed(2) : '0.00'}</span>
								</td>
							</tr>
							<tr>
								<td><strong>Acil:</strong></td>
								<td>${data.custom_acil_durum == 1 ? '<span class="badge badge-danger">ACİL</span>' : '<span class="badge badge-success">NORMAL</span>'}</td>
							</tr>
							<tr>
								<td><strong>Açıklama:</strong></td>
								<td>${data.aciklama || '-'}</td>
							</tr>
						</table>
					</div>
				</div>
			</div>
		</div>
		
		<div class="row mt-3">
			<div class="col-12 text-center">
				<a href="/app/sales-order/${data.sales_order}" target="_blank" class="btn btn-primary btn-lg">
					<i class="fa fa-external-link mr-2"></i>Siparişi Görüntüle
				</a>
			</div>
		</div>
	`;
	
	content.html(html);
}

// Virtual Scrolling System - Büyük tablolarda performans için
class VirtualScroller {
    constructor(container, rowHeight = 40, buffer = 5) {
        this.container = container;
        this.rowHeight = rowHeight;
        this.buffer = buffer;
        this.data = [];
        this.scrollTop = 0;
        this.containerHeight = 0;
        this.visibleRows = 0;
        this.startIndex = 0;
        this.endIndex = 0;
        
        this.init();
    }
    
    init() {
        this.container.style.position = 'relative';
        this.container.style.overflow = 'auto';
        
        // Scroll event listener
        this.container.addEventListener('scroll', this.handleScroll.bind(this));
        
        // Resize observer
        this.resizeObserver = new ResizeObserver(() => {
            this.updateDimensions();
        });
        this.resizeObserver.observe(this.container);
        
        this.updateDimensions();
    }
    
    updateDimensions() {
        this.containerHeight = this.container.clientHeight;
        this.visibleRows = Math.ceil(this.containerHeight / this.rowHeight);
        this.render();
    }
    
    setData(data) {
        this.data = data;
        this.render();
    }
    
    handleScroll() {
        this.scrollTop = this.container.scrollTop;
        this.render();
    }
    
    render() {
        if (!this.data.length) return;
        
        // Hangi satırların görünür olduğunu hesapla
        this.startIndex = Math.floor(this.scrollTop / this.rowHeight);
        this.endIndex = Math.min(
            this.startIndex + this.visibleRows + this.buffer * 2,
            this.data.length
        );
        
        // Buffer ekle
        this.startIndex = Math.max(0, this.startIndex - this.buffer);
        
        // Container'ı temizle
        this.container.innerHTML = '';
        
        // Toplam yüksekliği ayarla (scroll bar için)
        const totalHeight = this.data.length * this.rowHeight;
        const spacer = document.createElement('div');
        spacer.style.height = `${totalHeight}px`;
        spacer.style.position = 'relative';
        this.container.appendChild(spacer);
        
        // Sadece görünen satırları render et
        for (let i = this.startIndex; i < this.endIndex; i++) {
            const row = this.createRow(this.data[i], i);
            row.style.position = 'absolute';
            row.style.top = `${i * this.rowHeight}px`;
            row.style.width = '100%';
            this.container.appendChild(row);
        }
    }
    
    createRow(data, index) {
        // Bu fonksiyon override edilecek
        const row = document.createElement('div');
        row.className = 'virtual-row';
        row.textContent = `Row ${index + 1}`;
        return row;
    }
    
    destroy() {
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        this.container.removeEventListener('scroll', this.handleScroll);
    }
}
