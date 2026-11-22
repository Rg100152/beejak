/* Beejak core — navigation, toasts, modals and small display preferences. */
(function () {
  'use strict';

  function closeToast(toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(16px)';
    setTimeout(function () { toast.remove(); }, 220);
  }

  function initToasts() {
    document.querySelectorAll('.toast').forEach(function (toast) {
      var close = toast.querySelector('.toast-close');
      if (close) close.addEventListener('click', function () { closeToast(toast); });
      setTimeout(function () { if (toast.isConnected) closeToast(toast); }, 6000);
    });
  }

  window.BeejakToast = function (message, kind) {
    var stack = document.getElementById('toast-stack');
    if (!stack) return;
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + (kind || 'info');
    toast.innerHTML = '<span class="toast-icon">' + (kind === 'success' ? '✓' : '!') +
      '</span><span></span><button class="toast-close" aria-label="Dismiss">×</button>';
    toast.children[1].textContent = message;
    stack.appendChild(toast);
    initToasts();
  };

  window.BeejakModal = {
    open: function (id) {
      var modal = document.getElementById(id);
      if (modal) modal.hidden = false;
    },
    close: function (id) {
      var modal = document.getElementById(id);
      if (modal) modal.hidden = true;
    }
  };

  function initModals() {
    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
      backdrop.addEventListener('click', function (event) {
        if (event.target === backdrop) backdrop.hidden = true;
      });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop').forEach(function (m) { m.hidden = true; });
      }
    });
  }

  function initNavigation() {
    var rail = document.getElementById('nav-rail');
    var shell = document.querySelector('.app-shell');
    var toggle = document.getElementById('rail-toggle');
    if (toggle && rail && shell) {
      toggle.addEventListener('click', function () {
        rail.classList.toggle('collapsed');
        shell.classList.toggle('rail-collapsed');
      });
    }
    var density = document.getElementById('theme-toggle');
    if (density) {
      density.addEventListener('click', function () {
        document.body.classList.toggle('dense');
        window.BeejakToast(document.body.classList.contains('dense') ? 'Compact workspace enabled' : 'Comfortable workspace restored', 'info');
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initToasts();
    initModals();
    initNavigation();
    if (window.BeejakUPI && window.BeejakUPI.renderAll) window.BeejakUPI.renderAll();
  });
})();
