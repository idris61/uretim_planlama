// Profil miktar hesaplama butonlarını ekle
function attachProfileCalcButtons() {
    const inputs = document.querySelectorAll('input[data-fieldname="custom_profile_length_qty"]');
    inputs.forEach((input) => {
        if (input.dataset.profileCalcAttached === '1') return;

        const wrapper = input.parentNode;
        if (!wrapper) return;

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-primary btn-sm profile-calc-btn';
        button.innerHTML = '📊 Miktar Hesapla';
        button.style.marginLeft = '10px';
        button.style.marginTop = '5px';

        button.addEventListener('click', () => calculateQuantityScoped(input));
        wrapper.appendChild(button);
        input.dataset.profileCalcAttached = '1';
    });
}

// Yerel ondalık/rakam ayraçlarını güvenli şekilde sayıya çevir
function parseLocaleNumber(raw) {
    if (raw === null || raw === undefined) return 0;
    let s = String(raw).trim();
    if (!s) return 0;
    
    s = s.replace(/[^0-9.,]/g, '');
    if (s.includes('.') && s.includes(',')) {
        s = s.replace(/\./g, '').replace(',', '.');
    } else if (s.includes(',')) {
        s = s.replace(',', '.');
    }
    
    const num = parseFloat(s);
    return isNaN(num) ? 0 : num;
}

// Hesaplamayı butona en yakın kapsamdaki alanlarla yap
function calculateQuantityScoped(originInput) {
    const container = originInput.closest('.modal') || originInput.closest('.form-grid') || originInput.closest('.grid-row') || document;

    const profileCheckbox = container.querySelector('input[data-fieldname="custom_is_profile"]');
    const lengthField = container.querySelector('input[data-fieldname="custom_profile_length_m"]');
    const lengthQtyField = container.querySelector('input[data-fieldname="custom_profile_length_qty"]');
    const qtyField = container.querySelector('input[data-fieldname="qty"]');
    const cfField = container.querySelector('input[data-fieldname="conversion_factor"]');

    // Kontroller
    if (!profileCheckbox || !profileCheckbox.checked) {
        frappe.msgprint('❌ Önce "Profil mi?" alanını işaretleyin!');
        return;
    }
    if (!lengthField || !lengthField.value) {
        frappe.msgprint('❌ "Profil Boyu (m)" alanını doldurun!');
        return;
    }
    if (!lengthQtyField || !lengthQtyField.value) {
        frappe.msgprint('❌ "Profil Boyu Adedi" alanını doldurun!');
        return;
    }
    if (!qtyField) {
        frappe.msgprint('❌ "Miktar" alanı bulunamadı!');
        return;
    }

    // Değerleri hesapla
    const length = parseLocaleNumber(lengthField.value) || 0;
    const qty = parseInt(String(lengthQtyField.value)) || 0;
    const conversionFactor = parseLocaleNumber(cfField && cfField.value) || 1;
    
    if (length <= 0 || qty <= 0) {
        frappe.msgprint('❌ Boy ve Adet değerleri 0\'dan büyük olmalı!');
        return;
    }
    
    const calculatedQty = (length * qty) / conversionFactor;

    // Grid satırı bilgilerini bul ve modeli güncelle
    const gridRowEl = originInput.closest('.grid-row');
    const cdt = gridRowEl ? gridRowEl.getAttribute('data-doctype') : null;
    const cdn = gridRowEl ? gridRowEl.getAttribute('data-name') : null;

    if (cdt && cdn && frappe && frappe.model && typeof frappe.model.set_value === 'function') {
        const updates = [frappe.model.set_value(cdt, cdn, 'qty', calculatedQty)];
        
        if (!isNaN(conversionFactor) && conversionFactor > 0) {
            updates.push(frappe.model.set_value(cdt, cdn, 'stock_qty', calculatedQty * conversionFactor));
        }
        
        Promise.all(updates).then(() => {
            frappe.msgprint(`✅ Miktar hesaplandı: ${length} × ${qty} = ${calculatedQty}`);
        }).catch(() => {
            frappe.msgprint('❌ Miktar alanı güncellenirken hata oluştu!');
        });
        return;
    }

    // Fallback: direkt input değerini güncelle
    try {
        qtyField.value = calculatedQty;
        qtyField.dispatchEvent(new Event('change', { bubbles: true }));
        frappe.msgprint(`✅ Miktar hesaplandı: ${length} × ${qty} = ${calculatedQty}`);
    } catch (error) {
        frappe.msgprint('❌ Miktar alanı güncellenirken hata oluştu!');
    }
}

// DOM değişikliklerini izle ve butonları ekle
const observer = new MutationObserver(() => {
    attachProfileCalcButtons();
});

try {
    observer.observe(document.body, { childList: true, subtree: true });
} catch (e) {
    // ignore
}

// İlk yüklemede dene
attachProfileCalcButtons();
