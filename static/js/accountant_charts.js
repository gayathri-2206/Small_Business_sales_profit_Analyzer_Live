fetch("/chart-data")
  .then(res => res.json())
  .then(data => {

    /* ===============================
       MONTHLY EXPENSE BAR CHART
    =============================== */
    new Chart(document.getElementById("monthlyExpenseChart"), {
      type: "bar",
      data: {
        labels: Object.keys(data.monthly_profit),
        datasets: [{
          label: "Monthly Expenses",
          data: Object.values(data.monthly_profit).map(v => Math.abs(v)),
          backgroundColor: "#ef4444"
        }]
      },
      options: {
        plugins: {
          legend: { labels: { color: "#e5e7eb" } }
        },
        scales: {
          x: { ticks: { color: "#e5e7eb" } },
          y: { ticks: { color: "#e5e7eb" } }
        }
      }
    });

    /* ===============================
       EXPENSE CATEGORY PIE CHART
    =============================== */
    new Chart(document.getElementById("expensePieChart"), {
      type: "pie",
      data: {
        labels: Object.keys(data.expense_categories),
        datasets: [{
          data: Object.values(data.expense_categories),
          backgroundColor: [
            "#ef4444", "#f59e0b", "#22c55e",
            "#3b82f6", "#8b5cf6"
          ]
        }]
      },
      options: {
        plugins: {
          legend: { labels: { color: "#e5e7eb" } }
        }
      }
    });

    /* ===============================
       ✅ REVENUE vs EXPENSE LINE CHART
    =============================== */
    const labels = Object.keys(data.daily_revenue);

    new Chart(document.getElementById("revenueExpenseChart"), {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Revenue",
            data: labels.map(d => data.daily_revenue[d] || 0),
            borderColor: "#22c55e",
            backgroundColor: "rgba(34,197,94,0.2)",
            tension: 0.3
          },
          {
            label: "Expenses",
            data: labels.map(d => data.daily_expense[d] || 0),
            borderColor: "#ef4444",
            backgroundColor: "rgba(239,68,68,0.2)",
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: "#e5e7eb" } }
        },
        scales: {
          x: {
            ticks: { color: "#e5e7eb" },
            grid: { color: "rgba(255,255,255,0.05)" }
          },
          y: {
            ticks: { color: "#e5e7eb" },
            grid: { color: "rgba(255,255,255,0.05)" }
          }
        }
      }
    });
    /* ===============================
   STACKED BAR: Revenue / Expense / Profit
=============================== */

// --- Aggregate daily data into monthly ---
const monthlyData = {};

Object.keys(data.daily_revenue).forEach(date => {
  const month = date.slice(0, 7); // YYYY-MM
  if (!monthlyData[month]) {
    monthlyData[month] = { revenue: 0, expense: 0, profit: 0 };
  }

  monthlyData[month].revenue += data.daily_revenue[date] || 0;
  monthlyData[month].expense += data.daily_expense[date] || 0;
  monthlyData[month].profit += data.daily_profit[date] || 0;
});

// --- Prepare chart arrays ---
const months = Object.keys(monthlyData);
const revenueVals = months.map(m => monthlyData[m].revenue);
const expenseVals = months.map(m => monthlyData[m].expense);
const profitVals  = months.map(m => monthlyData[m].profit);

// --- Create stacked bar chart ---
new Chart(document.getElementById("stackedFinanceChart"), {
  type: "bar",
  data: {
    labels: months,
    datasets: [
      {
        label: "Revenue",
        data: revenueVals,
        backgroundColor: "#22c55e"
      },
      {
        label: "Expenses",
        data: expenseVals,
        backgroundColor: "#ef4444"
      },
      {
        label: "Profit",
        data: profitVals,
        backgroundColor: "#3b82f6"
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        labels: { color: "#e5e7eb" }
      }
    },
    scales: {
      x: {
        stacked: true,
        ticks: { color: "#e5e7eb" },
        grid: { color: "rgba(255,255,255,0.05)" }
      },
      y: {
        stacked: true,
        ticks: { color: "#e5e7eb" },
        grid: { color: "rgba(255,255,255,0.05)" }
      }
    }
  }
});


  });
