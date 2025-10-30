document.addEventListener('DOMContentLoaded', function() {
    const chartElement = document.getElementById('fleetStatusChart');
    if (chartElement) {
        try {
            const chartData = JSON.parse(document.getElementById('chart-data').textContent);
            const ctx = chartElement.getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: chartData,
                        backgroundColor: ['#4CAF50', '#FFC107', '#F44336'],
                        // --- INÍCIO DA CORREÇÃO ---
                        borderColor: '#ffffff', // Cor do espaçamento (branco)
                        borderWidth: 4,          // Largura do espaçamento
                        // --- FIM DA CORREÇÃO ---
                        cutout: '75%'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        } catch (e) { console.error("Falha ao renderizar o gráfico:", e); }
    }

    function setupModal(buttonId, modalId) {
        const openBtn = document.getElementById(buttonId);
        const modal = document.getElementById(modalId);
        if (openBtn && modal) {
            openBtn.addEventListener('click', () => modal.classList.add('active'));
        }
    }

    setupModal('open-maintenance-modal', 'maintenance-modal');
    setupModal('open-route-modal', 'register-route-modal');
    
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });
    flatpickr(".datetimepicker", { enableTime: true, dateFormat: "d/m/Y H:i", time_24hr: true, locale: "pt" });

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(btn => btn.addEventListener('click', () => modal.classList.remove('active')));
        modal.addEventListener('click', function(event) { if (event.target === modal) modal.classList.remove('active'); });
    });
});