document.addEventListener('DOMContentLoaded', function () {
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    const addVehicleModal = document.getElementById('add-vehicle-modal');
    const deactivateModal = document.getElementById('deactivate-vehicle-modal');
    const detailsModal = document.getElementById('vehicle-details-modal');

    const vehicleForm = document.getElementById('vehicle-form');
    const deactivateForm = document.getElementById('deactivate-form');

    function buildMaintenanceHistory(panel, data) {
        let html = `<h4>Histórico de Manutenção</h4>`;
        const totalCostBRL = data.total_cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        html += `<p class="history-summary">Custo Total: ${totalCostBRL}</p>`;

        if (data.history.length === 0) {
            html += '<p>Nenhum registro de manutenção concluída encontrado.</p>';
        } else {
            html += `
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Serviço</th>
                            <th>Mecânica</th>
                            <th>Data Conclusão</th>
                            <th>Custo</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.history.map(m => `
                            <tr>
                                <td>${m.service_type}</td>
                                <td>${m.shop_name}</td>
                                <td>${m.end_date}</td>
                                <td>${m.cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }
        panel.innerHTML = html;
    }

    function buildRouteHistory(panel, data) {
        let html = `<h4>Histórico de Rotas</h4>`;
        const totalDistance = data.stats.total_distance.toFixed(2).replace('.', ',');
        const totalRoutes = data.stats.total_routes;
        const totalFuelCostBRL = data.stats.total_fuel_cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        const totalTollCostBRL = data.stats.total_toll_cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        html += `<p class="history-summary">
                    Total: ${totalRoutes} rotas / ${totalDistance} km<br>
                    Custo Combustível (Est.): ${totalFuelCostBRL}<br>
                    Custo Pedágio (Est.): ${totalTollCostBRL}
                 </p>`;

        if (data.history.length === 0) {
            html += '<p>Nenhum registro de rota concluída encontrado.</p>';
        } else {
            html += `
                <div class="table-wrapper"> 
                    <table class="history-table">
                        <thead>
                            <tr>
                                <th>Rota</th>
                                <th>Data Conclusão</th>
                                <th>Distância</th>
                                <th>Combustível (Est.)</th>
                                <th>Pedágio (Est.)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.history.map(r => `
                                <tr>
                                    <td>${r.start_location} → ${r.end_location}</td>
                                    <td>${r.end_time}</td>
                                    <td>${r.distance.toFixed(2).replace('.', ',')} km</td>
                                    <td>${r.fuel_cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                    <td>${r.toll_cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        panel.innerHTML = html;
    }

    function fetchHistory(vehiclePk, historyType, panelId) {
        const panel = document.getElementById(panelId);
        if (!panel.querySelector('.history-loading')) return;

        fetch(`/vehicles/${vehiclePk}/${historyType}/`)
            .then(response => {
                if (!response.ok) throw new Error('Falha ao buscar dados.');
                return response.json();
            })
            .then(data => {
                if (historyType === 'maintenance_history') {
                    buildMaintenanceHistory(panel, data);
                } else if (historyType === 'route_history') {
                    buildRouteHistory(panel, data);
                }
            })
            .catch(error => {
                console.error('Erro ao buscar histórico:', error);
                panel.innerHTML = '<p style="color: red;">Erro ao carregar o histórico. Tente novamente.</p>';
            });
    }

    const openAddVehicleBtn = document.getElementById('open-add-vehicle-modal');
    if (openAddVehicleBtn && addVehicleModal) {
        openAddVehicleBtn.addEventListener('click', () => {
            if (vehicleForm) {
                vehicleForm.reset();
                vehicleForm.action = `/vehicles/add/`;
            }
            addVehicleModal.querySelector('#vehicle-modal-title').textContent = 'Adicionar Novo Veículo';
            addVehicleModal.querySelector('#vehicle-submit-button').textContent = 'Salvar Veículo';
            addVehicleModal.classList.add('active');
        });
    }

    const vehicleTableBody = document.querySelector('.vehicle-table tbody');
    if (vehicleTableBody) {
        vehicleTableBody.addEventListener('click', function (event) {
            const targetLink = event.target.closest('a.action-link');
            if (!targetLink) return;

            const row = targetLink.closest('tr');
            if (!row || !row.dataset.pk) return;

            const pk = row.dataset.pk;

            if (targetLink.classList.contains('action-view') && detailsModal) {
                event.preventDefault();
                detailsModal.dataset.currentPk = pk;
                document.getElementById('tab-panel-maintenance').innerHTML = '<p class="history-loading">Carregando histórico...</p>';
                document.getElementById('tab-panel-routes').innerHTML = '<p class="history-loading">Carregando histórico...</p>';
                detailsModal.querySelectorAll('.modal-tab-panel').forEach(p => p.style.display = 'none');
                detailsModal.querySelector('#tab-panel-details').style.display = 'block';
                detailsModal.querySelectorAll('.modal-tab-link').forEach(t => t.classList.remove('active'));
                detailsModal.querySelector('.modal-tab-link[data-target="tab-panel-details"]').classList.add('active');

                detailsModal.querySelector('#details-plate').textContent = row.dataset.plate;
                detailsModal.querySelector('#details-model-year').textContent = `${row.dataset.model} (${row.dataset.year})`;
                const statusTag = detailsModal.querySelector('#details-status-tag');
                statusTag.textContent = row.dataset.status_display;
                statusTag.className = `status-tag status-${row.dataset.status}`;
                detailsModal.querySelector('#details-model').textContent = row.dataset.model;
                detailsModal.querySelector('#details-year').textContent = row.dataset.year;
                detailsModal.querySelector('#details-mileage').textContent = `${row.dataset.mileage} km`;
                const acqDate = row.dataset.acquisition_date;
                try {
                    detailsModal.querySelector('#details-acquisition-date').textContent = new Date(acqDate + 'T00:00:00').toLocaleDateString('pt-BR');
                } catch (e) {
                    detailsModal.querySelector('#details-acquisition-date').textContent = 'Data inválida';
                    console.error("Error parsing acquisition date:", e);
                }
                detailsModal.querySelector('#details-driver-name').textContent = row.dataset.driver_name;
                const avgConsumption = row.dataset.average_fuel_consumption;
                const consumptionEl = detailsModal.querySelector('#details-avg-consumption');
                if (avgConsumption && avgConsumption > 0) {
                    consumptionEl.textContent = `${avgConsumption.replace('.', ',')} Km/L`;
                } else {
                    consumptionEl.textContent = 'Não informado';
                }
                detailsModal.classList.add('active');
            }

            if (targetLink.classList.contains('action-edit') && addVehicleModal && vehicleForm) {
                event.preventDefault();
                addVehicleModal.querySelector('#vehicle-modal-title').textContent = 'Editar Veículo';
                addVehicleModal.querySelector('#vehicle-submit-button').textContent = 'Salvar Alterações';
                addVehicleModal.querySelector('#id_plate').value = row.dataset.plate || '';
                addVehicleModal.querySelector('#id_model').value = row.dataset.model || '';
                addVehicleModal.querySelector('#id_year').value = row.dataset.year || '';
                addVehicleModal.querySelector('#id_acquisition_date').value = row.dataset.acquisition_date || '';
                addVehicleModal.querySelector('#id_initial_mileage').value = row.dataset.mileage || '';
                const avgConsumptionField = addVehicleModal.querySelector('#id_average_fuel_consumption');
                if (avgConsumptionField) {
                    avgConsumptionField.value = row.dataset.average_fuel_consumption || '';
                }
                vehicleForm.action = `/vehicles/${pk}/update/`;
                addVehicleModal.classList.add('active');
                if (addVehicleModal.querySelector('.datepicker')._flatpickr) {
                    addVehicleModal.querySelector('.datepicker')._flatpickr.setDate(row.dataset.acquisition_date, false, 'Y-m-d');
                }
            }

            if (targetLink.classList.contains('action-delete') && deactivateModal && deactivateForm) {
                event.preventDefault();
                deactivateForm.action = `/vehicles/${pk}/deactivate/`;
                deactivateModal.classList.add('active');
            }
        });
    }


    if (detailsModal) {
        detailsModal.addEventListener('click', function (e) {
            const tabLink = e.target.closest('.modal-tab-link');
            if (!tabLink) return;

            e.preventDefault();
            const targetPanelId = tabLink.dataset.target;
            const targetPanel = document.getElementById(targetPanelId);
            if (!targetPanel) return;

            detailsModal.querySelectorAll('.modal-tab-link').forEach(tab => tab.classList.remove('active'));
            tabLink.classList.add('active');

            detailsModal.querySelectorAll('.modal-tab-panel').forEach(panel => panel.style.display = 'none');
            targetPanel.style.display = 'block';

            const vehiclePk = detailsModal.dataset.currentPk;
            if (targetPanelId === 'tab-panel-maintenance') {
                fetchHistory(vehiclePk, 'maintenance_history', targetPanelId);
            } else if (targetPanelId === 'tab-panel-routes') {
                fetchHistory(vehiclePk, 'route_history', targetPanelId);
            }
        });
    }

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(button => button.addEventListener('click', () => modal.classList.remove('active')));
        modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });
    });
});