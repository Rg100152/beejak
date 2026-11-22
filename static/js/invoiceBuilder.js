/* Beejak split-studio — live A4 mirror, GST math and UPI QR updates. */
(function () {
  'use strict';

  var stateEl = document.getElementById('invoice-state');
  var form = document.getElementById('invoice-form');
  if (!stateEl || !form) return;

  var state = JSON.parse(stateEl.textContent || '{}');
  var itemsHost = document.getElementById('editor-items');
  var paperItems = document.getElementById('paper-items');
  var paper = document.getElementById('invoice-paper');
  var qrTimer = null;
  var currentTotal = 0;

  var ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen'];
  var TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

  function f(id) { return document.getElementById(id); }
  function value(id) { var el = f(id); return el ? String(el.value || '').trim() : ''; }
  function num(id) { var n = parseFloat(value(id)); return isFinite(n) ? n : 0; }
  function escapeHtml(text) {
    return String(text == null ? '' : text).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function symbol(code) { return code === 'USD' ? '$' : code === 'EUR' ? '€' : '₹'; }
  function money(amount, code) {
    try {
      return new Intl.NumberFormat(code === 'INR' ? 'en-IN' : 'en-US', {
        style: 'currency', currency: code || 'INR', minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Number(amount || 0));
    } catch (error) {
      return symbol(code) + Number(amount || 0).toFixed(2);
    }
  }
  function fmtDate(iso) {
    if (!iso) return '—';
    var parts = String(iso).split('-');
    if (parts.length !== 3) return iso;
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return parts[2] + ' ' + months[parseInt(parts[1], 10) - 1] + ' ' + parts[0];
  }
  function twoDigits(n) {
    if (n < 20) return ONES[n] || '';
    var tens = Math.floor(n / 10), ones = n % 10;
    return [TENS[tens], ONES[ones]].filter(Boolean).join(' ');
  }
  function words(amount) {
    var number = Math.abs(Number(amount || 0));
    var rupees = Math.floor(number);
    var paise = Math.round((number - rupees) * 100);
    if (paise === 100) { rupees += 1; paise = 0; }
    if (rupees === 0 && paise === 0) return 'Zero Only';
    var parts = [];
    var crore = Math.floor(rupees / 10000000); rupees %= 10000000;
    var lakh = Math.floor(rupees / 100000); rupees %= 100000;
    var thousand = Math.floor(rupees / 1000); rupees %= 1000;
    var hundred = Math.floor(rupees / 100); var rest = rupees % 100;
    if (crore) parts.push(twoDigits(crore) + ' Crore');
    if (lakh) parts.push(twoDigits(lakh) + ' Lakh');
    if (thousand) parts.push(twoDigits(thousand) + ' Thousand');
    if (hundred) parts.push(ONES[hundred] + ' Hundred');
    if (rest) parts.push(twoDigits(rest));
    var text = parts.join(' ') || 'Zero';
    if (paise) text += ' and ' + twoDigits(paise) + ' Paise';
    return text + ' Only';
  }

  function readItems() {
    return Array.prototype.map.call(itemsHost.querySelectorAll('.editor-item-row'), function (row) {
      return {
        description: row.querySelector('.item-desc').value || 'Service',
        qty: parseFloat(row.querySelector('.item-qty').value) || 0,
        unit_price: parseFloat(row.querySelector('.item-price').value) || 0
      };
    });
  }

  function renderEditorItems(items) {
    itemsHost.innerHTML = '';
    (items && items.length ? items : [{ description: '', qty: 1, unit_price: 0 }]).forEach(function (item) {
      var row = document.createElement('div');
      row.className = 'editor-item-row';
      row.innerHTML =
        '<input class="item-desc" placeholder="Service or item" value="' + escapeHtml(item.description || '') + '">' +
        '<input class="item-qty" type="number" min="0" step="0.5" value="' + (item.qty || 0) + '">' +
        '<input class="item-price" type="number" min="0" step="0.01" value="' + (item.unit_price || 0) + '">' +
        '<button class="item-remove" type="button" title="Remove item">×</button>';
      row.querySelector('.item-remove').addEventListener('click', function () {
        if (itemsHost.querySelectorAll('.editor-item-row').length > 1) { row.remove(); update(); }
      });
      itemsHost.appendChild(row);
    });
  }

  function calculate(items, discountPct, taxPct, mode) {
    var subtotal = 0;
    var normalised = items.map(function (item) {
      var line = Math.round(((item.qty || 0) * (item.unit_price || 0)) * 100) / 100;
      subtotal = Math.round((subtotal + line) * 100) / 100;
      return { description: item.description, qty: item.qty, unit_price: item.unit_price, line_total: line };
    });
    var discount = Math.round(subtotal * (discountPct || 0) * 100) / 10000;
    var taxable = Math.round(Math.max(0, subtotal - discount) * 100) / 100;
    var tax = Math.round(taxable * (taxPct || 0) * 100) / 10000;
    var cgst = 0, sgst = 0, igst = 0;
    if (mode === 'IGST') {
      igst = tax;
    } else {
      cgst = Math.round(tax * 100) / 200;
      sgst = Math.round((tax - cgst) * 100) / 100;
    }
    return {
      items: normalised, subtotal: subtotal, discount: discount, taxable: taxable,
      tax: tax, cgst: cgst, sgst: sgst, igst: igst,
      total: Math.round((taxable + tax) * 100) / 100
    };
  }

  function setFields(name, text) {
    document.querySelectorAll('#invoice-paper [data-field="' + name + '"]').forEach(function (node) {
      node.textContent = text;
    });
  }

  function syncHiddenItems(items) {
    var hidden = f('items-json');
    if (hidden) hidden.value = JSON.stringify(items || []);
  }

  function refreshQr(code, upi, invoiceNo, amount) {
    clearTimeout(qrTimer);
    qrTimer = setTimeout(function () {
      if (!window.BeejakUPI) return;
      var uri = window.BeejakUPI.buildUri({
        upiId: upi, amount: amount, currency: code, note: invoiceNo
      });
      var box = document.getElementById('upi-pay-box');
      if (box) box.setAttribute('data-upi-uri', uri);
      window.BeejakUPI.render(f('upi-qr'), uri, 86);
    }, 170);
  }

  function update() {
    var items = readItems();
    var code = value('f-currency') || 'INR';
    var mode = value('f-tax-mode') === 'IGST' ? 'IGST' : 'CGST_SGST';
    var t = calculate(items, num('f-discount'), num('f-tax'), mode);
    currentTotal = t.total;
    var invoiceNo = value('f-invoice-no');
    var upi = value('f-upi');

    setFields('invoice_no', invoiceNo || '—');
    setFields('issue_date', fmtDate(value('f-issue-date')));
    setFields('due_date', fmtDate(value('f-due-date')));
    setFields('currency', code);
    setFields('client_name', value('f-client-name') || 'Client name');
    setFields('client_company', value('f-client-company') || '—');
    setFields('client_email', value('f-client-email') || '—');
    setFields('notes', value('f-notes') || '—');
    setFields('upi_id', upi);
    setFields('discount_pct', num('f-discount'));
    setFields('tax_pct', num('f-tax'));
    setFields('subtotal', money(t.subtotal, code));
    setFields('discount_amount', '−' + money(t.discount, code));
    setFields('taxable_amount', money(t.taxable, code));
    setFields('cgst', money(t.cgst, code));
    setFields('sgst', money(t.sgst, code));
    setFields('igst', money(t.igst, code));
    setFields('grand_total', money(t.total, code));
    setFields('upi_amount', money(t.total, code));
    setFields('amount_words', words(t.total));

    if (paperItems) {
      var sign = symbol(code);
      paperItems.innerHTML = t.items.map(function (item) {
        return '<tr><td>' + escapeHtml(item.description) + '</td><td>' + item.qty +
          '</td><td>' + sign + Number(item.unit_price).toFixed(2) +
          '</td><td>' + sign + Number(item.line_total).toFixed(2) + '</td></tr>';
      }).join('');
    }
    var subtotalLabel = document.getElementById('editor-subtotal');
    if (subtotalLabel) subtotalLabel.textContent = money(t.subtotal, code);
    var meta = document.getElementById('preview-meta');
    if (meta) meta.textContent = invoiceNo + ' · ' + code;

    if (paper) {
      paper.classList.toggle('tax-igst', mode === 'IGST');
      paper.classList.toggle('tax-cgst', mode !== 'IGST');
      paper.classList.remove('accent-emerald', 'accent-navy', 'accent-saffron');
      var checked = form.querySelector('input[name="accent"]:checked');
      paper.classList.add('accent-' + (checked ? checked.value : 'emerald'));
      var chip = paper.querySelector('[data-field="status"]');
      if (chip) {
        chip.textContent = state.status || 'DRAFT';
        chip.className = 'status-chip on-paper status-' + String(state.status || 'DRAFT').toLowerCase();
      }
      if ((state.status || '') === 'PAID') {
        var seal = document.getElementById('paid-seal');
        if (seal) seal.hidden = false;
      }
    }

    syncHiddenItems(items);
    refreshQr(code, upi, invoiceNo, t.total);
  }

  function init() {
    renderEditorItems(state.items || []);
    form.addEventListener('input', update);
    form.addEventListener('change', update);
    form.addEventListener('submit', function () { syncHiddenItems(readItems()); });

    var add = document.getElementById('add-item');
    if (add) add.addEventListener('click', function () {
      var row = document.createElement('div');
      row.className = 'editor-item-row';
      row.innerHTML =
        '<input class="item-desc" placeholder="New service or item" value="">' +
        '<input class="item-qty" type="number" min="0" step="0.5" value="1">' +
        '<input class="item-price" type="number" min="0" step="0.01" value="0">' +
        '<button class="item-remove" type="button" title="Remove item">×</button>';
      row.querySelector('.item-remove').addEventListener('click', function () {
        if (itemsHost.querySelectorAll('.editor-item-row').length > 1) { row.remove(); update(); }
      });
      itemsHost.appendChild(row);
      row.querySelector('.item-desc').focus();
      update();
    });

    var pick = f('f-client-pick');
    if (pick) pick.addEventListener('change', function () {
      var option = pick.options[pick.selectedIndex];
      if (!option || !option.value) return;
      f('f-client-id').value = option.value;
      f('f-client-name').value = option.getAttribute('data-name') || '';
      f('f-client-company').value = option.getAttribute('data-company') || '';
      f('f-client-email').value = option.getAttribute('data-email') || '';
      update();
    });

    var printTop = document.getElementById('preview-print-top');
    if (printTop) printTop.addEventListener('click', function () { syncHiddenItems(readItems()); window.print(); });

    var sendOpen = document.getElementById('send-open-top');
    if (sendOpen) sendOpen.addEventListener('click', function () {
      var warning = document.getElementById('send-warning');
      var confirm = document.getElementById('send-confirm');
      var sendForm = document.getElementById('send-form');
      var email = document.getElementById('send-email');
      var message = document.getElementById('send-message');
      if (email) email.value = value('f-client-email');
      if (message) {
        message.value = 'Hi ' + (value('f-client-name') || 'there') + ',\n\nPlease find your invoice ' +
          value('f-invoice-no') + ' for ' + money(currentTotal, value('f-currency')) +
          ' attached. You can scan the UPI QR on the invoice for instant payment.\n\n' +
          'Thank you for your business!\nRaj Gautam · Jaunpur, Uttar Pradesh';
      }
      if (!state.id) {
        if (warning) warning.hidden = false;
        if (confirm) confirm.disabled = true;
      } else {
        if (warning) warning.hidden = true;
        if (confirm) confirm.disabled = false;
        if (sendForm) sendForm.action = '/invoices/' + state.id + '/send';
      }
      window.BeejakModal.open('send-modal');
    });

    ['send-close', 'send-cancel'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('click', function () { window.BeejakModal.close('send-modal'); });
    });

    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
