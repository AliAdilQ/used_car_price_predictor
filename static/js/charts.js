document.addEventListener('DOMContentLoaded', () => {
  const wrapper = document.querySelector('[data-charts]');
  if (!wrapper || typeof Chart === 'undefined') return;
  const data = JSON.parse(wrapper.dataset.charts);
  Chart.defaults.font.family = "Manrope, 'Segoe UI', sans-serif";
  Chart.defaults.font.size = 9;
  Chart.defaults.color = '#92a185';
  const scales = {
    x: { grid: { display: false }, border: { display: false }, ticks: { maxRotation: 0 } },
    y: { beginAtZero: true, grid: { color: '#edf1e6' }, border: { display: false }, ticks: { precision: 0, padding: 8 } },
  };
  new Chart(document.getElementById('activity-chart'), {
    type: 'line',
    data: { labels: data.activity.labels, datasets: [{ data: data.activity.values, borderColor: '#5f946e', backgroundColor: '#edf5e9', fill: true, tension: .35, pointRadius: 3, pointBackgroundColor: '#fff', pointBorderWidth: 2, borderWidth: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, scales, plugins: { legend: { display: false }, tooltip: { displayColors: false, callbacks: { label: (context) => `${context.parsed.y} predictions` } } } },
  });
  new Chart(document.getElementById('brand-chart'), {
    type: 'bar',
    data: { labels: data.brands.labels, datasets: [{ data: data.brands.values, backgroundColor: data.brands.labels.map((_, index) => index === 0 ? '#538868' : '#cedfc4'), borderRadius: 4, barThickness: 13 }] },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', scales: {
      x: { ...scales.y, ticks: { precision: 0 }, grid: { color: '#f0f3eb' } },
      y: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 8 } } },
    }, plugins: { legend: { display: false }, tooltip: { displayColors: false, callbacks: { label: (context) => `${context.parsed.x} predictions` } } } },
  });
});
