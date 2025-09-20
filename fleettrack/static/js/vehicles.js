document.addEventListener('DOMContentLoaded', function() {
    // Inicializa os calendários em qualquer campo com a classe .datepicker
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    // --- REFERÊNCIAS A TODOS OS MODAIS E FORMULÁRIOS ---
    const addVehicleModal = document.getElementById('add-vehicle-modal');
    const deactivateModal = document.getElementById('deactivate-vehicle-modal');
    const detailsModal = document.getElementById('vehicle-details-modal');
    const historyModal = document.getElementById('history-vehicle-modal');
    const maintenanceDetailsModal = document.getElementById('maintenance-details-modal');
    const routeHistoryModal = document.getElementById('route-history-modal');
    const routeDetailsModal = document.getElementById('route-details-modal');

    const vehicleForm = document.getElementById('vehicle-form');
    const deactivateForm = document.getElementById('deactivate-form');

    // Variável para guardar a linha do veículo ativo para navegação entre modais
    let activeVehicleRow = null;

    // --- FUNÇÕES AUXILIARES ---
    function showMaintenanceHistoryModal(row) {
        const plate = row.dataset.plate;
        historyModal.querySelector('h2').textContent = `Histórico de Manutenção de ${plate}`;
        const historyListContainer = document.getElementById('history-list-container');
        historyListContainer.innerHTML = '<p>A carregar histórico...</p>';
        
        const maintenanceData = row.querySelector('.vehicle-maintenance-data');
        const items = maintenanceData.querySelectorAll('.maint-item');
        
        if (items.length > 0) {
            let htmlContent = '<ul class="history-list">';
            items.forEach(item => {
                htmlContent += `<li data-maint-pk="${item.dataset.maintPk}" style="cursor: pointer;"><span class="history-date">${item.dataset.date}</span><span class="history-service">${item.dataset.service}</span></li>`;
            });
            htmlContent += '</ul>';
            historyListContainer.innerHTML = htmlContent;
        } else {
            historyListContainer.innerHTML = '<p>Nenhum registo de manutenção encontrado.</p>';
        }
        historyModal.classList.add('active');
    }

    function showRouteHistoryModal(row) {
        const plate = row.dataset.plate;
        routeHistoryModal.querySelector('h2').textContent = `Histórico de Viagens de ${plate}`;
        const routeListContainer = document.getElementById('route-list-container');
        routeListContainer.innerHTML = '<p>A carregar histórico...</p>';
        
        const routeData = row.querySelector('.vehicle-route-data');
        const items = routeData.querySelectorAll('.route-item');
        
        if (items.length > 0) {
            let htmlContent = '<ul class="route-history-list">';
            items.forEach(item => {
                htmlContent += `
                    <li data-route-pk="${item.dataset.routePk}" style="cursor: pointer;">
                        <span class="route-location">${item.dataset.start_location} → ${item.dataset.end_location}</span>
                        <span class="route-date">${item.dataset.start_time}</span>
                        <span class="status-tag status-${item.dataset.statusSlug}">${item.dataset.statusDisplay}</span>
                    </li>`;
            });
            htmlContent += '</ul>';
            routeListContainer.innerHTML = htmlContent;
        } else {
            routeListContainer.innerHTML = '<p>Nenhum registo de viagem encontrado.</p>';
        }
        routeHistoryModal.classList.add('active');
    }
    
    // --- EVENTOS DE BOTÕES E AÇÕES ---

    // Botão "+ Adicionar Veículo"
    document.getElementById('open-add-vehicle-modal').addEventListener('click', () => {
        vehicleForm.reset();
        addVehicleModal.querySelector('#vehicle-modal-title').textContent = 'Adicionar Novo Veículo';
        addVehicleModal.querySelector('#vehicle-submit-button').textContent = 'Salvar Veículo';
        vehicleForm.action = `/vehicles/add/`;
        addVehicleModal.classList.add('active');
    });

    // Botão "Ver Histórico de Manutenção" (no modal de detalhes)
    document.getElementById('view-maintenance-history-btn').addEventListener('click', () => {
        if (activeVehicleRow) {
            detailsModal.classList.remove('active');
            showMaintenanceHistoryModal(activeVehicleRow);
        }
    });
    
    // Botão "Ver Histórico de Viagens" (no modal de detalhes)
    document.getElementById('view-route-history-btn').addEventListener('click', () => {
        if (activeVehicleRow) {
            detailsModal.classList.remove('active');
            showRouteHistoryModal(activeVehicleRow);
        }
    });

    // Clique na lista de histórico de MANUTENÇÃO
    document.getElementById('history-list-container').addEventListener('click', function(event) {
        const listItem = event.target.closest('li');
        if (!listItem) return;
        const maintPk = listItem.dataset.maintPk;
        const maintDataItem = document.querySelector(`.maint-item[data-maint-pk='${maintPk}']`);
        if (maintDataItem) {
            document.getElementById('maintenance-details-content').innerHTML = `
                <dl class="maintenance-details-grid">
                    <dt>Serviço:</dt><dd>${maintDataItem.dataset.service}</dd>
                    <dt>Início:</dt><dd>${maintDataItem.dataset.start_date}</dd>
                    <dt>Fim:</dt><dd>${maintDataItem.dataset.end_date}</dd>
                    <dt>Mecânica:</dt><dd>${maintDataItem.dataset.mechanic_shop_name}</dd>
                    <dt>Custo (R$):</dt><dd>${maintDataItem.dataset.estimated_cost}</dd>
                    <dt>KM no Serviço:</dt><dd>${maintDataItem.dataset.current_mileage}</dd>
                    <dt>Observações:</dt><dd>${maintDataItem.dataset.notes || 'Nenhuma'}</dd>
                </dl>`;
            historyModal.classList.remove('active');
            maintenanceDetailsModal.classList.add('active');
        }
    });
    
    // Clique na lista de histórico de VIAGENS
    document.getElementById('route-list-container').addEventListener('click', function(event) {
        const listItem = event.target.closest('li');
        if (!listItem) return;
        const routePk = listItem.dataset.routePk;
        const routeDataItem = document.querySelector(`.route-item[data-route-pk='${routePk}']`);
        if (routeDataItem) {
            document.getElementById('route-details-content').innerHTML = `
                <dl class="maintenance-details-grid">
                    <dt>Partida:</dt><dd>${routeDataItem.dataset.start_location}</dd>
                    <dt>Chegada:</dt><dd>${routeDataItem.dataset.end_location}</dd>
                    <dt>Início:</dt><dd>${routeDataItem.dataset.start_time}</dd>
                    <dt>Fim:</dt><dd>${routeDataItem.dataset.end_time}</dd>
                    <dt>Motorista:</dt><dd>${routeDataItem.dataset.driverName}</dd>
                    <dt>Status:</dt><dd>${routeDataItem.dataset.statusDisplay}</dd>
                </dl>`;
            routeHistoryModal.classList.remove('active');
            routeDetailsModal.classList.add('active');
        }
    });
    
    // Botões "Voltar"
    document.getElementById('back-to-details-btn').addEventListener('click', () => { historyModal.classList.remove('active'); detailsModal.classList.add('active'); });
    document.getElementById('back-to-history-btn').addEventListener('click', () => { maintenanceDetailsModal.classList.remove('active'); historyModal.classList.add('active'); });
    document.getElementById('back-to-details-from-route-btn').addEventListener('click', () => { routeHistoryModal.classList.remove('active'); detailsModal.classList.add('active'); });
    document.getElementById('back-to-route-history-btn').addEventListener('click', () => { routeDetailsModal.classList.remove('active'); routeHistoryModal.classList.add('active'); });

    // Ações na tabela (👁️, ✏️, 🗑️)
    document.querySelector('.vehicle-table tbody').addEventListener('click', function(event) {
        const target = event.target.closest('a');
        if (!target) return;
        activeVehicleRow = target.closest('tr');
        const pk = activeVehicleRow.dataset.pk;

        // Ação: VISUALIZAR DETALHES (👁️)
        if (target.classList.contains('action-view')) {
            event.preventDefault();
            document.getElementById('details-plate').textContent = activeVehicleRow.dataset.plate;
            document.getElementById('details-model-year').textContent = `${activeVehicleRow.dataset.model} (${activeVehicleRow.dataset.year})`;
            const statusTag = document.getElementById('details-status-tag');
            statusTag.textContent = activeVehicleRow.dataset.status_display;
            statusTag.className = `status-tag status-${activeVehicleRow.dataset.status}`;
            document.getElementById('details-model').textContent = activeVehicleRow.dataset.model;
            document.getElementById('details-year').textContent = activeVehicleRow.dataset.year;
            document.getElementById('details-mileage').textContent = `${activeVehicleRow.dataset.mileage} km`;
            const driverName = activeVehicleRow.dataset.driver_name;
            document.getElementById('details-driver-name').textContent = driverName;
            document.getElementById('details-driver-avatar').textContent = driverName !== 'Não atribuído' ? driverName.slice(0, 2).toUpperCase() : 'NA';
            const lastMaint = activeVehicleRow.querySelector('.maint-item:last-child');
            document.getElementById('details-last-maintenance').textContent = lastMaint ? lastMaint.dataset.date : 'Nenhum registo';
            detailsModal.classList.add('active');
        }

        // Ação: EDITAR (✏️)
        if (target.classList.contains('action-edit')) {
            event.preventDefault();
            const vehicleModalTitle = document.getElementById('vehicle-modal-title');
            const vehicleSubmitButton = document.getElementById('vehicle-submit-button');
            vehicleModalTitle.textContent = 'Editar Veículo';
            vehicleSubmitButton.textContent = 'Salvar Alterações';
            
            document.querySelector('#add-vehicle-modal #id_plate').value = activeVehicleRow.dataset.plate;
            document.querySelector('#add-vehicle-modal #id_model').value = activeVehicleRow.dataset.model;
            document.querySelector('#add-vehicle-modal #id_year').value = activeVehicleRow.dataset.year;
            document.querySelector('#add-vehicle-modal #id_acquisition_date').value = activeVehicleRow.dataset.acquisition_date;
            document.querySelector('#add-vehicle-modal #id_mileage').value = activeVehicleRow.dataset.mileage;
            document.querySelector('#add-vehicle-modal #id_status').value = activeVehicleRow.dataset.status;

            vehicleForm.action = `/vehicles/${pk}/update/`;
            addVehicleModal.classList.add('active');
        }

        // Ação: DESATIVAR (🗑️)
        if (target.classList.contains('action-delete')) {
            event.preventDefault();
            deactivateForm.action = `/vehicles/${pk}/deactivate/`;
            deactivateModal.classList.add('active');
        }
    });

    // --- LÓGICA GENÉRICA PARA FECHAR MODAIS ---
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(button => button.addEventListener('click', () => modal.classList.remove('active')));
        modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });
    });
});