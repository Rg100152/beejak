/* Beejak UPI engine — builds standard NPCI deep links and paints crisp QR codes.
   Uses the vendored, offline qrcode.min.js in static/js/vendor/. */
(function () {
  'use strict';

  var PAYEE = 'Raj Gautam';
  var DEFAULT_UPI = 'rajgautam@upi';

  function buildUri(options) {
    var opts = options || {};
    var params = {
      pa: String(opts.upiId || DEFAULT_UPI).trim(),
      pn: opts.payeeName || PAYEE,
      am: Number(opts.amount || 0).toFixed(2),
      cu: opts.currency || 'INR',
      tn: opts.note || ''
    };
    return 'upi://pay?' + Object.keys(params).map(function (key) {
      return key + '=' + encodeURIComponent(params[key]);
    }).join('&');
  }

  function render(element, text, size) {
    if (!element) return;
    var px = size || 92;
    element.innerHTML = '';
    if (!window.QRCode) return;
    try {
      new window.QRCode(element, {
        text: text,
        width: px,
        height: px,
        colorDark: '#0F172A',
        colorLight: '#FFFFFF',
        correctLevel: window.QRCode.CorrectLevel.M
      });
    } catch (error) {
      element.textContent = 'QR unavailable';
    }
  }

  function renderAll() {
    document.querySelectorAll('[data-upi-uri]').forEach(function (host) {
      var target = host.id === 'upi-qr' || host.id === 'checkout-qr'
        ? host
        : host.querySelector('.upi-qr-frame, .checkout-qr');
      var uri = host.getAttribute('data-upi-uri');
      if (target && uri) render(target, uri, target.id === 'checkout-qr' ? 110 : 86);
    });
  }

  window.BeejakUPI = {
    buildUri: buildUri,
    render: render,
    renderAll: renderAll
  };

  document.addEventListener('DOMContentLoaded', renderAll);
})();
