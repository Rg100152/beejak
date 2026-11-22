/* Beejak Pay Sandbox — 3-step simulated checkout with DB sync and PAID stamp. */
(function () {
  'use strict';

  var stateEl = document.getElementById('pay-state');
  if (!stateEl) return;
  var state = JSON.parse(stateEl.textContent || '{}');
  var method = 'UPI';
  var paper = document.getElementById('invoice-paper');
  var submit = document.getElementById('pay-submit');
  var methodPanel = document.getElementById('pay-panel-method');
  var processingPanel = document.getElementById('pay-panel-processing');
  var successPanel = document.getElementById('pay-panel-success');

  function step(number, status) {
    var el = document.querySelector('.step[data-step="' + number + '"]');
    if (!el) return;
    el.classList.remove('active', 'done');
    el.classList.add(status);
  }

  function showSuccess(payload) {
    step(2, 'done');
    step(3, 'active');
    if (methodPanel) methodPanel.hidden = true;
    if (processingPanel) processingPanel.hidden = true;
    if (successPanel) successPanel.hidden = false;
    var utrNode = document.getElementById('success-utr');
    if (utrNode) utrNode.textContent = payload.utr;
    var link = document.getElementById('success-receipt');
    if (link) link.href = payload.receipt_url || ('/receipt/' + payload.utr);

    if (paper) {
      paper.classList.add('is-paid');
      var seal = document.getElementById('paid-seal');
      if (seal) {
        seal.hidden = false;
        var sealUtr = seal.querySelector('[data-field="utr"]');
        if (sealUtr) sealUtr.textContent = payload.utr;
      }
      var chip = paper.querySelector('[data-field="status"]');
      if (chip) {
        chip.textContent = 'PAID';
        chip.className = 'status-chip on-paper status-paid';
      }
    }
  }

  function init() {
    document.querySelectorAll('.method-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        document.querySelectorAll('.method-tab').forEach(function (t) { t.classList.remove('active'); });
        document.querySelectorAll('.method-content').forEach(function (c) { c.classList.remove('active'); });
        tab.classList.add('active');
        method = tab.getAttribute('data-method') || 'UPI';
        var content = document.querySelector('.method-content[data-content="' + method + '"]');
        if (content) content.classList.add('active');
      });
    });

    if (submit) submit.addEventListener('click', function () {
      submit.disabled = true;
      if (methodPanel) methodPanel.hidden = true;
      if (processingPanel) processingPanel.hidden = false;
      step(1, 'done');
      step(2, 'active');

      setTimeout(function () {
        fetch('/api/pay/' + state.invoice_id, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
          body: JSON.stringify({ method: method, amount: state.amount })
        })
          .then(function (response) { return response.json(); })
          .then(function (payload) {
            if (!payload.ok) throw new Error(payload.error || 'Payment failed');
            showSuccess(payload);
          })
          .catch(function (error) {
            submit.disabled = false;
            if (methodPanel) methodPanel.hidden = false;
            if (processingPanel) processingPanel.hidden = true;
            if (window.BeejakToast) window.BeejakToast('Demo payment failed: ' + error.message, 'error');
          });
      }, 1500);
    });

    if (String(state.status || '').toUpperCase() === 'PAID') {
      var existing = paper && paper.querySelector('#paid-seal [data-field="utr"]');
      var utr = existing ? existing.textContent.trim() : '';
      if (utr && utr !== '—') {
        showSuccess({ utr: utr, receipt_url: '/receipt/' + utr });
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
