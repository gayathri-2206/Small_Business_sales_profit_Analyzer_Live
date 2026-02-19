fetch("/staff/chart-data")
  .then(res => res.json())
  .then(data => {

    /* ================= Today Sales Bar Chart ================= */
    if (document.getElementById("staffTodaySales")) {
      new Chart(document.getElementById("staffTodaySales"), {
        type: "bar",
        data: {
          labels: Object.keys(data.today_sales),
          datasets: [{
            label: "Quantity Sold",
            data: Object.values(data.today_sales),
            backgroundColor: "#22c55e",
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                stepSize: 1,
                color: "#e5e7eb"
              },
              grid: {
                color: "rgba(255,255,255,0.1)"
              },
              title: {
                display: true,
                text: "Quantity",
                color: "#e5e7eb"
              }
            },
            x: {
              ticks: {
                color: "#e5e7eb"
              },
              grid: {
                display: false
              },
              title: {
                display: true,
                text: "Items",
                color: "#e5e7eb"
              }
            }
          },
          plugins: {
            legend: {
              labels: { color: "#e5e7eb" }
            },
            tooltip: {
              enabled: true
            }
          }
        }
      });
    }

    /* ================= Expense Category Pie Chart ================= */
    if (document.getElementById("staffExpensePie")) {
      new Chart(document.getElementById("staffExpensePie"), {
        type: "pie",
        data: {
          labels: Object.keys(data.expense_categories),
          datasets: [{
            data: Object.values(data.expense_categories),
            backgroundColor: [
              "#ef4444",
              "#22c55e",
              "#f59e0b",
              "#3b82f6",
              "#8b5cf6",
              "#64748b"
            ],
            borderWidth: 2,
            borderColor: "#020617"
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "bottom",
              labels: {
                color: "#e5e7eb",
                padding: 20
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const total = context.dataset.data.reduce((a, b) => a + b, 0);
                  const value = context.raw;
                  const percent = ((value / total) * 100).toFixed(1);
                  return `${context.label}: ₹${value} (${percent}%)`;
                }
              }
            }
          }
        }
      });
    }

  });
