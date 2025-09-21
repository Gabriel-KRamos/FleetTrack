// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    
    // =================================================================
    // LÓGICA DO GRÁFICO DE STATUS DA FROTA (AGORA DINÂMICO)
    // =================================================================
    const chartElement = document.getElementById('fleetStatusChart');
    if (chartElement) {
        const ctx = chartElement.getContext('2d');
        
        // Verifica se a variável chartData existe e se há veículos para exibir
        const totalVehicles = (chartData.available || 0) + (chartData.on_route || 0) + (chartData.in_maintenance || 0);

        if (typeof chartData !== 'undefined' && totalVehicles > 0) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Disponível', 'Em Rota', 'Em Manutenção'],
                    datasets: [{
                        label: 'Status da Frota',
                        // Usa os dados dinâmicos passados pelo Django
                        data: [chartData.available, chartData.on_route, chartData.in_maintenance],
                        backgroundColor: [
                            '#4CAF50', // Verde para Disponível
                            '#FFC107', // Amarelo para Em Rota
                            '#F44336'  // Vermelho para Em Manutenção
                        ],
                        borderColor: '#FFFFFF',
                        borderWidth: 4,
                        cutout: '75%'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }

    // =================================================================
    // LÓGICA DO MODAL DE MANUTENÇÃO
    // =================================================================
    const maintenanceModal = document.getElementById('maintenance-modal');
    const openMaintenanceBtn = document.getElementById('open-maintenance-modal');
    if (openMaintenanceBtn && maintenanceModal) {
        openMaintenanceBtn.addEventListener('click', () => maintenanceModal.classList.add('active'));
        maintenanceModal.querySelectorAll('.close-modal, #cancel-modal-btn').forEach(btn => {
            btn.addEventListener('click', () => maintenanceModal.classList.remove('active'));
        });
    }

    // =================================================================
    // LÓGICA DO MODAL DE REGISTRAR ROTA
    // =================================================================
    const routeModal = document.getElementById('register-route-modal');
    const openRouteBtn = document.getElementById('open-route-modal');
    if (openRouteBtn && routeModal) {
        openRouteBtn.addEventListener('click', () => routeModal.classList.add('active'));
        routeModal.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => routeModal.classList.remove('active'));
        });
    }

    // =================================================================
    // INICIALIZAÇÃO DOS CALENDÁRIOS (FLATPICKR)
    // =================================================================
    flatpickr(".datepicker", {
        dateFormat: "d/m/Y",
        locale: "pt",
    });

    flatpickr(".datetimepicker", {
        enableTime: true,
        dateFormat: "d/m/Y H:i",
        time_24hr: true,
        locale: "pt",
    });

    // =================================================================
    // INICIALIZAÇÃO DO MAPA (LEAFLET.JS) COM DADOS DINÂMICOS
    // =================================================================
    const mapElement = document.getElementById('live-map');
    if (mapElement) {
        const mapCenter = [-23.5505, -46.6333];
        const map = L.map('live-map').setView(mapCenter, 10);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        if (typeof routeData !== 'undefined' && routeData.length > 0) {
            routeData.forEach(route => {
                L.marker([route.lat, route.lng]).addTo(map)
                    .bindPopup(`<b>${route.driver}</b><br>Placa: ${route.plate}`);
            });
        }
    }

    // =================================================================
    // FUNÇÃO GENÉRICA PARA FECHAR MODAIS CLICANDO NO FUNDO
    // =================================================================
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});