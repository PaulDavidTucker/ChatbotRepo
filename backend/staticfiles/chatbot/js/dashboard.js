//dashboard.html
function copyApiKey(apiKey) {
  navigator.clipboard.writeText(apiKey).then(function () {
    // Show toast notification
    showToast("API Key copied to clipboard!", "success");
  });
}

function copyEmbedCode() {
  const embedCode = document.getElementById("embedCode").textContent;
  navigator.clipboard.writeText(embedCode).then(function () {
    showToast("Embed code copied to clipboard!", "success");
  });
}

function showToast(message, type = "info") {
  // Create toast element
  const toast = document.createElement("div");
  toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  toast.style.top = "20px";
  toast.style.right = "20px";
  toast.style.zIndex = "9999";
  toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(toast);

  // Auto remove after 3 seconds
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 3000);
}

function initializeCharts() {
  // Usage Chart
  const usageCtx = document.getElementById("usageChart");
  if (usageCtx && chartData.usage) {
    new Chart(usageCtx, {
      type: "line",
      data: {
        labels: chartData.usage.labels,
        datasets: [
          {
            label: "Messages",
            data: chartData.usage.data,
            borderColor: "rgb(75, 192, 192)",
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }

  // Domains Chart
  const domainsCtx = document.getElementById("domainsChart");
  if (domainsCtx && chartData.domains) {
    new Chart(domainsCtx, {
      type: "doughnut",
      data: {
        labels: chartData.domains.labels,
        datasets: [
          {
            data: chartData.domains.data,
            backgroundColor: [
              "#FF6384",
              "#36A2EB",
              "#FFCE56",
              "#4BC0C0",
              "#9966FF",
            ],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }
}

function setupNewClientForm() {
  const form = document.getElementById("newClientForm");
  if (form) {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(form);
      const data = {
        name: formData.get("name"),
        email: formData.get("email"),
        allowed_domains: formData.get("domains")
          ? formData
              .get("domains")
              .split(",")
              .map((d) => d.trim())
          : [],
        config: {
          title: formData.get("title"),
          primary_color: formData.get("primary_color"),
          welcome_message: formData.get("welcome_message"),
          system_prompt: formData.get("system_prompt"),
        },
      };

      try {
        const response = await fetch("/api/clients/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        if (response.ok) {
          const result = await response.json();
          showToast("Client created successfully!", "success");
          setTimeout(() => location.reload(), 1500);
        } else {
          showToast("Error creating client", "danger");
        }
      } catch (error) {
        showToast("Error creating client", "danger");
      }
    });
  }
}

function viewSessionMessages(sessionId) {
  // This would open a modal or navigate to a detailed session view
  // For now, just show a placeholder
  showToast("Session message view coming soon!", "info");
}
