/* Beejak — dependency-free canvas charts for the revenue dashboard. */
(function () {
  'use strict';

  function setup(canvas) {
    var ratio = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    var width = rect.width || canvas.width;
    var height = rect.height || 200;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    var ctx = canvas.getContext('2d');
    ctx.scale(ratio, ratio);
    return { ctx: ctx, width: width, height: height };
  }

  function maxOf(values) {
    return Math.max.apply(null, values.concat([1]));
  }

  function drawRevenue() {
    var canvas = document.getElementById('revenue-chart');
    if (!canvas) return;
    var labels = JSON.parse(canvas.getAttribute('data-labels') || '[]');
    var billed = JSON.parse(canvas.getAttribute('data-billed') || '[]');
    var collected = JSON.parse(canvas.getAttribute('data-collected') || '[]');
    var s = setup(canvas);
    var ctx = s.ctx, w = s.width, h = s.height;
    var pad = { left: 44, right: 12, top: 14, bottom: 30 };
    var plotH = h - pad.top - pad.bottom;
    var plotW = w - pad.left - pad.right;
    var peak = maxOf(billed.concat(collected));

    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(148,163,184,0.13)';
    ctx.fillStyle = 'rgba(148,163,184,0.75)';
    ctx.font = '10px system-ui, sans-serif';
    ctx.lineWidth = 1;
    for (var i = 0; i <= 4; i++) {
      var y = pad.top + plotH - (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
      var tick = Math.round(peak / 4 * i);
      ctx.fillText(tick >= 1000 ? (tick / 1000).toFixed(0) + 'k' : String(tick), 6, y + 3);
    }

    var count = labels.length || 1;
    var slot = plotW / count;
    var barW = Math.max(8, Math.min(20, slot / 3));
    billed.forEach(function (value, index) {
      var x = pad.left + slot * index + slot / 2 - barW - 1;
      var bh = (value / peak) * plotH;
      var ch = ((collected[index] || 0) / peak) * plotH;
      ctx.fillStyle = '#38BDF8';
      ctx.fillRect(x, pad.top + plotH - bh, barW, bh);
      ctx.fillStyle = '#10B981';
      ctx.fillRect(x + barW + 2, pad.top + plotH - ch, barW, ch);
      ctx.fillStyle = 'rgba(148,163,184,0.85)';
      ctx.textAlign = 'center';
      ctx.fillText(labels[index] || '', pad.left + slot * index + slot / 2, h - 9);
    });
    ctx.textAlign = 'left';
  }

  function drawDonut() {
    var canvas = document.getElementById('status-chart');
    if (!canvas) return;
    var data = JSON.parse(canvas.getAttribute('data-breakdown') || '[]');
    var colors = { PAID: '#10B981', SENT: '#38BDF8', DRAFT: '#94A3B8', OVERDUE: '#F43F5E' };
    var total = data.reduce(function (sum, row) { return sum + row.count; }, 0);
    var s = setup(canvas);
    var ctx = s.ctx, cx = s.width / 2, cy = s.height / 2;
    var radius = Math.min(cx, cy) - 12;
    ctx.clearRect(0, 0, s.width, s.height);
    if (!total) {
      ctx.strokeStyle = 'rgba(148,163,184,.25)';
      ctx.lineWidth = 18;
      ctx.beginPath(); ctx.arc(cx, cy, radius - 9, 0, Math.PI * 2); ctx.stroke();
      return;
    }
    var start = -Math.PI / 2;
    data.forEach(function (row) {
      var angle = (row.count / total) * Math.PI * 2;
      ctx.strokeStyle = colors[row.status] || '#64748B';
      ctx.lineWidth = 18;
      ctx.beginPath();
      ctx.arc(cx, cy, radius - 9, start, start + angle - 0.02);
      ctx.stroke();
      start += angle;
    });
    ctx.fillStyle = '#E8EFF9';
    ctx.font = '700 22px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(String(total), cx, cy + 7);
    ctx.textAlign = 'left';
  }

  function render() { drawRevenue(); drawDonut(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
  else render();
  window.addEventListener('resize', render);
})();
