document.addEventListener('DOMContentLoaded', function() {
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    // --- REFERÊNCIAS AOS MODAIS ---
    const addVehicleModal = document.getElementById('add-vehicle-modal');
    const deactivateModal = document.getElementById('deactivate-vehicle-modal');
    const detailsModal = document.getElementById('vehicle-details-modal');
    const historyModal = document.getElementById('history-vehicle-modal');
    const maintenanceDetailsModal = document.getElementById('maintenance-details-modal');

    let activeVehicleRow = null; // Guarda a linha do veículo ativo para navegação entre modais

    // --- FUNÇÕES ---
    function showHistoryModal(row) {
        const plate = row.dataset.plate;
        historyModal.querySelector('h2').textContent = `Histórico de ${plate}`;
        const historyListContainer = document.getElementById('history-list-container');
        historyListContainer.innerHTML = '<p>A carregar histórico...</p>';
        
        const maintenanceData = row.querySelector('.vehicle-maintenance-data');
        const items = maintenanceData.querySelectorAll('.maint-item');
        
        if (items.length > 0) {
            let htmlContent = '<ul class="history-list">';
            items.forEach(item => {
                htmlContent += `<li data-maint-pk="${item.dataset.maintPk}"><span class="history-date">${item.dataset.date}</span><span class="history-service">${item.dataset.service}</span></li>`;
            });
            htmlContent += '</ul>';
            historyListContainer.innerHTML = htmlContent;
        } else {
            historyListContainer.innerHTML = '<p>Nenhum registo de manutenção encontrado.</p>';
        }
        historyModal.classList.add('active');
    }

    // --- EVENTOS DE BOTÕES E AÇÕES ---

    // Botão "+ Adicionar Veículo"
    document.getElementById('open-add-vehicle-modal').addEventListener('click', () => { /* ... Lógica de adicionar ... */ });

    // Botão "Ver Histórico" (DENTRO do modal de detalhes)
    document.getElementById('view-maintenance-history-btn').addEventListener('click', () => {
        if (activeVehicleRow) {
            showHistoryModal(activeVehicleRow);
            detailsModal.classList.remove('active');
        }
    });

    // Clique num item da lista de histórico para ver detalhes
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
    
    // Botões "Voltar"
    document.getElementById('back-to-history-btn').addEventListener('click', () => {
        maintenanceDetailsModal.classList.remove('active');
        historyModal.classList.add('active');
    });
    document.getElementById('back-to-details-btn').addEventListener('click', () => {
        historyModal.classList.remove('active');
        detailsModal.classList.add('active');
    });

    // Ações na tabela (👁️, ✏️, 🗑️)
    document.querySelector('.vehicle-table tbody').addEventListener('click', function(event) {
        const target = event.target.closest('a');
        if (!target) return;
        const row = target.closest('tr');
        activeVehicleRow = row;
        const pk = row.dataset.pk;

        if (target.classList.contains('action-view')) {
            event.preventDefault();
            document.getElementById('details-plate').textContent = row.dataset.plate;
            document.getElementById('details-model-year').textContent = `${row.dataset.model} (${row.dataset.year})`;
            const statusTag = document.getElementById('details-status-tag');
            statusTag.textContent = row.dataset.status_display;
            statusTag.className = `status-tag status-${row.dataset.status}`;
            document.getElementById('details-model').textContent = row.dataset.model;
            document.getElementById('details-year').textContent = row.dataset.year;
            document.getElementById('details-mileage').textContent = `${row.dataset.mileage} km`;
            const driverName = row.dataset.driver_name;
            document.getElementById('details-driver-name').textContent = driverName;
            document.getElementById('details-driver-avatar').textContent = driverName !== 'Não atribuído' ? driverName.slice(0, 2).toUpperCase() : 'NA';
            const lastMaint = row.querySelector('.maint-item:last-child');
            document.getElementById('details-last-maintenance').textContent = lastMaint ? lastMaint.dataset.date : 'Nenhum registo';
            document.getElementById('view-maintenance-history-btn').dataset.vehiclePk = pk;
            detailsModal.classList.add('active');
        }
        // ... (Lógica para Editar e Desativar)
    });

    // Lógica para fechar modais
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(button => button.addEventListener('click', () => modal.classList.remove('active')));
        modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });
    });
});