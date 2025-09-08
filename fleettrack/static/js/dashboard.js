// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    
    // =================================================================
    // LÓGICA DO GRÁFICO DE STATUS DA FROTA
    // =================================================================
    const chartElement = document.getElementById('fleetStatusChart');
    if (chartElement) {
        const ctx = chartElement.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Disponível', 'Em Rota', 'Em Manutenção'],
                datasets: [{
                    label: 'Status da Frota',
                    data: [45, 35, 20],
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

document.addEventListener('DOMContentLoaded', function() {
    
    // ... (todo o código existente do gráfico e dos modais) ...

    // =================================================================
    // INICIALIZAÇÃO DO MAPA (LEAFLET.JS)
    // =================================================================
    const mapElement = document.getElementById('live-map');
    if (mapElement) {
        // Coordenadas para centrar o mapa (ex: São Paulo)
        const mapCenter = [-23.5505, -46.6333];

        // Cria o mapa
        const map = L.map('live-map').setView(mapCenter, 10); // O '10' é o nível de zoom

        // Adiciona a camada de "azulejos" do OpenStreetMap (gratuito)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Adiciona marcadores de exemplo
        L.marker([-23.55, -46.63]).addTo(map)
            .bindPopup('<b>John Smith</b><br>Em Rota');
        L.marker([-23.60, -46.69]).addTo(map)
            .bindPopup('<b>Sarah Johnson</b><br>Disponível');
        L.marker([-23.50, -46.70]).addTo(map)
            .bindPopup('<b>Mike Chen</b><br>Em Rota');
    }
});