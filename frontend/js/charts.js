/**
 * SoloBiz AI — Chart.js Visualizations Manager
 */

let monthlyTrendChartInstance = null;
let categoryChartInstance = null;

const CATEGORY_COLORS = {
  Software: "#6366f1",            // Indigo
  Travel: "#06b6d4",              // Cyan
  Equipment: "#a855f7",           // Purple
  Marketing: "#f59e0b",           // Amber
  "Office Supplies": "#10b981",    // Emerald
  "Legal & Professional": "#f43f5e", // Rose
  Utilities: "#0ea5e9",           // Sky
  Other: "#94a3b8",               // Slate
};

export function renderMonthlyTrendChart(canvasId, monthlyTrends = []) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  if (monthlyTrendChartInstance) {
    monthlyTrendChartInstance.destroy();
  }

  // Create smooth gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, 260);
  gradient.addColorStop(0, "rgba(99, 102, 241, 0.45)");
  gradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");

  const labels = monthlyTrends.map((t) => t.month);
  const data = monthlyTrends.map((t) => t.total_amount);

  monthlyTrendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels.length > 0 ? labels : ["No data yet"],
      datasets: [
        {
          label: "Spending ($)",
          data: data.length > 0 ? data : [0],
          borderColor: "#6366f1",
          borderWidth: 3,
          backgroundColor: gradient,
          fill: true,
          tension: 0.38,
          pointBackgroundColor: "#ffffff",
          pointBorderColor: "#6366f1",
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#f8fafc",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255, 255, 255, 0.12)",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label(context) {
              return ` Total: $${Number(context.raw).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#64748b", font: { size: 11 } },
        },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#64748b",
            font: { size: 11 },
            callback(val) {
              return `$${val}`;
            },
          },
        },
      },
    },
  });
}

export function renderCategoryChart(canvasId, categoryBreakdown = []) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  const labels = categoryBreakdown.map((c) => c.category);
  const data = categoryBreakdown.map((c) => c.total_amount);
  const colors = categoryBreakdown.map((c) => CATEGORY_COLORS[c.category] || "#94a3b8");

  categoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels.length > 0 ? labels : ["No data"],
      datasets: [
        {
          data: data.length > 0 ? data : [1],
          backgroundColor: colors.length > 0 ? colors : ["#334155"],
          borderWidth: 2,
          borderColor: "#0f172a",
          hoverOffset: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            padding: 14,
            usePointStyle: true,
            font: { size: 11 },
          },
        },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#f8fafc",
          bodyColor: "#94a3b8",
          borderColor: "rgba(255, 255, 255, 0.12)",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label(context) {
              const val = Number(context.raw);
              return ` ${context.label}: $${val.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
            },
          },
        },
      },
    },
  });
}
