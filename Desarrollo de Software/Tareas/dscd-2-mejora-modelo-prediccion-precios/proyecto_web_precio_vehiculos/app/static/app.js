const form = document.getElementById('predict-form');
const result = document.getElementById('result');
const kpiCount = document.getElementById('kpi-count');
const kpiAverage = document.getElementById('kpi-average');
const kpiMax = document.getElementById('kpi-max');
const priceChart = document.getElementById('price-chart');
const historyBody = document.getElementById('history-body');
const historyTable = document.getElementById('history-table');
const historyEmpty = document.getElementById('history-empty');
const refreshHistoryButton = document.getElementById('refresh-history');
const API_BASE = window.API_BASE || '';

function formatCurrency(value) {
  return `$${Number(value).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function renderPriceChart(rows) {
  const hasRows = rows.length > 0;
  priceChart.classList.toggle('hidden', !hasRows);

  if (!hasRows) {
    priceChart.innerHTML = '';
    return;
  }

  const maxPrice = Math.max(...rows.map((row) => Number(row.estimated_price)));

  priceChart.innerHTML = rows
    .map((row) => {
      const price = Number(row.estimated_price);
      const height = Math.max(12, Math.round((price / Math.max(maxPrice, 1)) * 100));
      return `
        <div class="metric-bar-group">
          <div class="metric-bar" style="height:${height}%" title="${formatCurrency(price)}"></div>
          <span class="metric-bar-label">${formatCurrency(price)}</span>
        </div>
      `;
    })
    .join('');
}

async function loadHistory() {
  try {
    const response = await fetch(`${API_BASE}/api/price-predictions?limit=5`);
    const rows = await response.json();

    if (!response.ok) {
      throw new Error(rows.detail || 'No se pudo cargar el historial');
    }

    historyBody.innerHTML = rows
      .map(
        (row) => `
          <tr>
            <td>${row.created_at}</td>
            <td>${row.marca}</td>
            <td>${row.modelo}</td>
            <td>${row.anio}</td>
            <td>${row.km}</td>
            <td>${row.transmision}</td>
            <td>${formatCurrency(row.estimated_price)}</td>
            <td>${row.model_version}</td>
          </tr>
        `,
      )
      .join('');

    const prices = rows.map((row) => Number(row.estimated_price));
    const count = rows.length;
    const average = count ? prices.reduce((sum, value) => sum + value, 0) / count : 0;
    const maxValue = count ? Math.max(...prices) : 0;

    kpiCount.textContent = String(count);
    kpiAverage.textContent = formatCurrency(average);
    kpiMax.textContent = formatCurrency(maxValue);
    renderPriceChart(rows);

    const hasRows = rows.length > 0;
    historyEmpty.classList.toggle('hidden', hasRows);
    historyTable.classList.toggle('hidden', !hasRows);
  } catch (error) {
    historyEmpty.textContent = `No se pudo cargar el historial: ${error.message}`;
    historyEmpty.classList.remove('hidden');
    historyTable.classList.add('hidden');
    priceChart.classList.add('hidden');
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const data = Object.fromEntries(new FormData(form));
  const payload = {
    marca: data.marca,
    modelo: data.modelo,
    anio: Number(data.anio),
    km: Number(data.km),
    transmision: data.transmision,
  };

  result.classList.remove('hidden');
  result.textContent = 'Calculando estimacion...';

  try {
    const response = await fetch(`${API_BASE}/predict-price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || 'Request failed');
    }

    result.innerHTML = `
      <strong>Precio estimado:</strong> ${formatCurrency(body.estimated_price)} ${body.currency}<br>
      <strong>Modelo:</strong> ${body.model_version}
    `;

    await loadHistory();
  } catch (error) {
    result.textContent = `Error: ${error.message}`;
  }
});

refreshHistoryButton.addEventListener('click', loadHistory);

loadHistory();
