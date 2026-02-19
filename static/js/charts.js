fetch("/chart-data")
  .then(res => res.json())
  .then(data => {

    /* ---------- Daily Profit ---------- */
    new Chart(document.getElementById("dailyProfit"), {
      type: "line",
      data: {
        labels: Object.keys(data.daily_profit),
        datasets: [{
          label: "Daily Profit",
          data: Object.values(data.daily_profit),
          borderColor: "#00ffcc",
          fill: false,
          tension: 0.3
        }]
      }
    });

    /* ---------- Monthly Profit ---------- */
    new Chart(document.getElementById("monthlyProfit"), {
      type: "bar",
      data: {
        labels: Object.keys(data.monthly_profit),
        datasets: [{
          label: "Monthly Profit",
          data: Object.values(data.monthly_profit),
          backgroundColor: "#4e73df"
        }]
      }
    });

    /* ---------- Yearly Profit (NEW) ---------- */
    new Chart(document.getElementById("yearlyProfit"), {
      type: "bar",
      data: {
        labels: Object.keys(data.yearly_profit),
        datasets: [{
          label: "Yearly Profit",
          data: Object.values(data.yearly_profit),
          backgroundColor: "#1cc88a"
        }]
      }
    });

    /* ---------- Expense Distribution ---------- */
    new Chart(document.getElementById("expensePie"), {
      type: "pie",
      data: {
        labels: Object.keys(data.expense_categories),
        datasets: [{
          data: Object.values(data.expense_categories),
          backgroundColor: [
            "#ff6384",
            "#36a2eb",
            "#ffce56",
            "#e74a3b",
            "#858796"
          ]
        }]
      }
    });

  });
  fetch("/ai-forecast")
.then(res => res.json())
.then(data => {
    const ctx = document.getElementById("aiForecastChart").getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.forecast.dates,
            datasets: [{
                label: "Predicted Profit (₹)",
                data: data.forecast.profits,
                borderWidth: 3,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });

    const list = document.getElementById("aiSuggestions");
    data.suggestions.forEach(s => {
        const li = document.createElement("li");
        li.style.padding = "10px";
        li.innerText = s;
        list.appendChild(li);
    });
});
fetch("/ai-forecast-advanced")
.then(res => res.json())
.then(data => {

    // MONTHLY
    new Chart(document.getElementById("monthlyAIChart"), {
        type: "line",
        data: {
            labels: data.monthly.labels,
            datasets: [
                {
                    label: "Predicted Income",
                    data: data.monthly.income,
                    borderColor: "#4ecdc4",
                    borderWidth: 3,
                    tension: 0.4
                },
                {
                    label: "Predicted Expense",
                    data: data.monthly.expense,
                    borderColor: "#ff6b6b",
                    borderWidth: 3,
                    tension: 0.4
                }
            ]
        }
    });

    // YEARLY
    new Chart(document.getElementById("yearlyAIChart"), {
        type: "line",
        data: {
            labels: data.yearly.labels,
            datasets: [
                {
                    label: "Yearly Income",
                    data: data.yearly.income,
                    borderColor: "#6ae0d8",
                    borderWidth: 4
                },
                {
                    label: "Yearly Expense",
                    data: data.yearly.expense,
                    borderColor: "#ff8e8e",
                    borderWidth: 4
                }
            ]
        }
    });

    const ul = document.getElementById("aiSuggestions");
    ul.innerHTML = "";
    data.suggestions.forEach(s => {
        const li = document.createElement("li");
        li.innerText = s;
        li.style.padding = "8px";
        ul.appendChild(li);
    });
});


