frappe.provide('uretim_planlama');

// Event listener'ları bir kere tanımla ve tekrar kullan
const eventOptions = { passive: true, capture: false };

frappe.ui.form.on('Production Plan', {
    refresh(frm) {
        setupFloatingPanel(frm);
        // Debounce the handler attachment
        frappe.utils.debounce(() => {
            if (frm.fields_dict['po_items']?.grid) {
                attachRowSelectionHandler(frm);
                updateSelectedTotalMtul(frm); // Başlangıçta ve refresh sonrası paneli güncelle
            }
        }, 500)(); // 500ms gecikme ile hemen zamanla
    },

    onload(frm) {
        setupFloatingPanel(frm);
        // Debounce the handler attachment
        frappe.utils.debounce(() => {
            if (frm.fields_dict['po_items']?.grid) {
                attachRowSelectionHandler(frm);
                updateSelectedTotalMtul(frm); // Başlangıçta ve onload sonrası paneli güncelle
            }
        }, 500)(); // 500ms gecikme ile hemen zamanla
    },

    after_save(frm) {
        // Kaydetme sonrası paneli gizle
        const panel = $('#montaj-ogeleri-panel');
        if (panel.length && panel.is(':visible')) {
            panel.hide();
        }
        // Seçili öğe özeti ve toplamı sıfırla
        $('#selected-total-mtul').text('0.00');
        // Panelin görünürlüğünü güncelle
        updateSelectedTotalMtul(frm);
    }
});

function setupFloatingPanel(frm) {
    if ($('#montaj-ogeleri-panel').length) return;

    const panelHtml = `
        <div id="montaj-ogeleri-panel" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 250px;
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            font-size: 13px;
            display: none; /* Başlangıçta gizli */
        ">
            <h6 style="margin-top: 0; margin-bottom: 10px;">Seçili Öğeler Özeti</h6>
            <p style="margin-bottom: 10px;">Toplam MTUL: <strong id="selected-total-mtul">0.00</strong></p>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="btn btn-sm btn-primary" id="assign-workstation-btn">İş İstasyonu Ata</button>
                <button class="btn btn-sm btn-primary" id="assign-start-date-btn">Başlangıç Tarihi Ata</button>
            </div>
        </div>
    `;

    $('body').append(panelHtml);
    
    // Event delegation kullan
    $(document).on('click', '#assign-workstation-btn', eventOptions, () => assignWorkstation(frm));
    $(document).on('click', '#assign-start-date-btn', eventOptions, () => assignStartDate(frm));
}

function attachRowSelectionHandler(frm) {
    const grid = frm.fields_dict['po_items']?.grid; // Optional chaining ekledim
    
    if (!grid) {
         return; // Grid objesi yoksa çık
    }

    if (grid.__has_selection_and_qty_handler) {
        return;
    }

    // Event delegation kullan
    $(document).on('change', '.grid-row-check', eventOptions, () => {
        updateSelectedTotalMtul(frm);
    });
    
    attachQtyChangeListeners(frm); // planned_qty listenerlarını ekle

    // Debounce the render handler
    grid.after_render = frappe.utils.debounce(() => {
         attachQtyChangeListeners(frm); // Render sonrası listenerları tekrar eklemeyi dene
         updateSelectedTotalMtul(frm); // Render sonrası paneli güncelle
    }, 100); // 100ms debounce gecikmesi
    
    grid.__has_selection_and_qty_handler = true;

}

const attachQtyChangeListeners = (frm) => {
    const grid = frm.fields_dict['po_items']?.grid; // Optional chaining ekledim
    if (!grid || !grid.grid_rows) {
        return;
    }

    grid.grid_rows.forEach(row => {
         attachQtyChangeListenersForRow(frm, row); // Her satır için listener eklemeyi dene
    });
};

// Sadece tek bir satır için listener eklemeyi deneyen yardımcı fonksiyon
const attachQtyChangeListenersForRow = (frm, row, retryCount = 0) => {
     const plannedQtyField = row?.fields_dict?.planned_qty;
     const rowName = row.doc.name || row.name;
     const maxRetries = 15; // Maksimum deneme sayısı artırıldı
     const retryDelay = 100; // Denemeler arası gecikme (ms)

     if (plannedQtyField?.wrapper) {
         // Event delegation kullan
         // planned_qty inputuna change listener ekle
         // Mevcut listener'ı kaldırıp yeniden ekliyoruz, böylece mükerrer olmasın
         const selector = `#${plannedQtyField.wrapper.id} input`;
         // .off().on() yapısını koru ama selector'ı doğru ayarla
         $(document).off('change', selector).on('change', selector, eventOptions, function() {
                const newPlannedQty = $(this).val(); // Input alanından yeni değeri al

                if (row.get_checked()) {
                     // Bu kısımda güncel row objesine ihtiyacımız var. frappe.model.get_doc kullanabiliriz.
                    const currentItemDoc = frappe.model.get_doc('Production Plan Item', rowName);
                    if (currentItemDoc) {
                         // Modeldeki planned_qty değerini güncelle
                        frappe.model.set_value('Production Plan Item', rowName, 'planned_qty', newPlannedQty)
                            .then(() => {
                                // Model güncellendikten sonra toplam MTUL'u yeniden hesapla
                                updateSelectedTotalMtul(frm);
                            })
                            .catch(error => {
                                frappe.show_alert({ message: `Hata: ${error.message}`, indicator: 'red' });
                            });
                    }
                }
         });

     } else if (retryCount < maxRetries) {
          // Alan bulunamazsa, kısa bir gecikmeyle tekrar dene (sadece bu satır için)
         setTimeout(() => {
             // Retry sırasında güncel row objesini bulmaya çalış
             const currentGridRows = frm.fields_dict['po_items']?.grid?.grid_rows;
             const updatedRow = currentGridRows?.find(r => (r.doc.name || r.name) === rowName);

             if (updatedRow) {
                 // Güncellenmiş row objesi ile tekrar dene
                 attachQtyChangeListenersForRow(frm, updatedRow, retryCount + 1);
             } else {
             }
         }, retryDelay); // Gecikme sonrası tekrar dene

     } else {
         frappe.show_alert({ message: `Hata: ${rowName} satırı için Planned Qty alanı bulunamadı.`, indicator: 'red' });
     }
};

function updateSelectedTotalMtul(frm) {
    const grid = frm.fields_dict['po_items']?.grid; // Optional chaining ekledim
    if (!grid) return; // Grid objesi yoksa çık

    const selectedItemNames = grid.get_selected();
    let totalMtul = 0;

    // Panel görünürlüğünü kontrol et
    const panel = $('#montaj-ogeleri-panel');
    if (selectedItemNames.length === 0) {
        if (panel.is(':visible')) {
             panel.hide();
        }
        $('#selected-total-mtul').text('0.00');
        return;
    } else {
         if (!panel.is(':visible')) {
             panel.show();
         }
    }

    selectedItemNames.forEach(itemName => {
        // frappe.model.get_doc burada modeldeki en güncel değeri almalı
        const itemDoc = frappe.model.get_doc('Production Plan Item', itemName);
        if (itemDoc) {
            const mtulPerPiece = parseFloat(itemDoc.custom_mtul_per_piece) || 0;
            // planned_qty değerini doğrudan itemDoc'tan al
            const plannedQty = parseFloat(itemDoc.planned_qty) || 0;
            totalMtul += mtulPerPiece * plannedQty;
        }
    });

    $('#selected-total-mtul').text(totalMtul.toFixed(2));
}

function assignWorkstation(frm) {
    const grid = frm.fields_dict['po_items']?.grid; // Optional chaining ekledim
    if (!grid) return; // Grid objesi yoksa çık

    const selectedItems = grid.get_selected();

    if (!selectedItems.length) {
        frappe.msgprint('Lütfen önce atanacak satırları seçin.');
        return;
    }

    const customWorkstationField = frappe.meta.get_docfield('Production Plan Item', 'custom_workstation', frm.doc.name);
    let workstationOptions = [];

    if (customWorkstationField?.options) {
        if (typeof customWorkstationField.options === 'string') {
            workstationOptions = customWorkstationField.options.includes(',') 
                ? customWorkstationField.options.split(',').map(o => o.trim())
                : customWorkstationField.options.split(/\r?\n/).map(o => o.trim());
        } else if (Array.isArray(customWorkstationField.options)) {
            workstationOptions = customWorkstationField.options.map(o => String(o).trim());
        }

        workstationOptions = workstationOptions.filter(o => o !== '');
        if (workstationOptions.length === 0 || workstationOptions[0] !== '') {
            workstationOptions.unshift('');
        }
    }

    if (workstationOptions.length <= 1 && workstationOptions[0] === '') {
        frappe.msgprint('İş İstasyonu alanında tanımlı seçenek bulunamadı.');
        return;
    }

    frappe.prompt([
        {
            label: 'Atanacak İş İstasyonu',
            fieldname: 'workstation',
            fieldtype: 'Select',
            options: workstationOptions,
            reqd: 0
        }
    ], (values) => {
        const workstation = values.workstation || '';
        
        selectedItems.forEach(itemName => {
            try {
                frappe.model.set_value('Production Plan Item', itemName, 'custom_workstation', workstation);
                const gridRow = grid.grid_rows.find(row => row.doc.name === itemName);
                if (gridRow) {
                    gridRow.refresh_field('custom_workstation');
                }
            } catch (error) {
                frappe.show_alert({ message: `Hata: ${error.message}`, indicator: 'red' });
            }
        });

        frappe.show_alert({ message: `${selectedItems.length} satıra İş İstasyonu atandı.`, indicator: 'green' });
         updateSelectedTotalMtul(frm); // MTUL toplamını güncelle
    }, 'İş İstasyonu Ata', 'Ata');
}

function assignStartDate(frm) {
    const grid = frm.fields_dict['po_items']?.grid; // Optional chaining ekledim
    if (!grid) return; // Grid objesi yoksa çık

    const selectedItems = grid.get_selected();

    if (!selectedItems.length) {
        frappe.msgprint('Lütfen önce atanacak satırları seçin.');
        return;
    }

    // Varsayılan tarihi bugünün tarihi ve saat 08:00 olarak ayarla
    const defaultStartDate = frappe.datetime.get_today() + ' 08:00:00';

    frappe.prompt([
        {
            label: 'Atanacak Başlangıç Tarihi',
            fieldname: 'start_date',
            fieldtype: 'Datetime',
            reqd: 1,
            default: defaultStartDate // Varsayılan değeri ekledik
        }
    ], (values) => {
        const startDate = values.start_date;
        
        selectedItems.forEach(itemName => {
            try {
                frappe.model.set_value('Production Plan Item', itemName, 'planned_start_date', startDate);
                const gridRow = grid.grid_rows.find(row => row.doc.name === itemName);
                if (gridRow) {
                    gridRow.refresh_field('planned_start_date');
                }
            } catch (error) {
                frappe.show_alert({ message: `Hata: ${error.message}`, indicator: 'red' });
            }
        });

        frappe.show_alert({ message: `${selectedItems.length} satıra Başlangıç Tarihi atandı.`, indicator: 'green' });
         updateSelectedTotalMtul(frm); // MTUL toplamını güncelle
    }, 'Başlangıç Tarihi Ata', 'Ata');
} 