document.addEventListener('DOMContentLoaded', function () {
    flatpickr(".datepicker", { dateFormat: "Y-m-d", locale: "pt" });

    const addDriverModal = document.getElementById('add-driver-modal');
    const demissionModal = document.getElementById('demission-modal');
    const detailsModal = document.getElementById('driver-details-modal');

    const driverForm = document.getElementById('driver-form');
    const demissionForm = document.getElementById('demission-form');

    function formatCNH(value) {
        if (!value) return '';
        let v = value.replace(/\D/g, '');
        if (v.length > 11) v = v.substring(0, 11);

        v = v.replace(/^(\d{3})(\d)/, '$1.$2');
        v = v.replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3');
        v = v.replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
        return v;
    }

    const cnhInput = document.getElementById('id_license_number');
    if (cnhInput) {
        cnhInput.addEventListener('input', function(e) {
            e.target.value = formatCNH(e.target.value);
        });
    }

    document.querySelectorAll('.license-tag').forEach(function(tag) {
        tag.textContent = formatCNH(tag.textContent);
    });

    const openAddDriverBtn = document.getElementById('open-add-driver-modal');
    if (openAddDriverBtn && addDriverModal) {
        openAddDriverBtn.addEventListener('click', () => {
            driverForm.reset();
            addDriverModal.querySelector('#driver-modal-title').textContent = 'Adicionar Novo Motorista';
            driverForm.action = `/drivers/add/`;
            addDriverModal.classList.add('active');
        });
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
                                <th>Veículo</th>
                                <th>Data Conclusão</th>
                                <th>Distância</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.history.map(r => `
                                <tr>
                                    <td>${r.start_location} → ${r.end_location}</td>
                                    <td>${r.vehicle_plate}</td>
                                    <td>${r.end_time}</td>
                                    <td>${r.distance.toFixed(2).replace('.', ',')} km</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
        panel.innerHTML = html;
    }

    function fetchHistory(driverPk, historyType, panelId) {
        const panel = document.getElementById(panelId);
        if (!panel.querySelector('.history-loading')) return;

        fetch(`/drivers/${driverPk}/${historyType}/`)
            .then(response => {
                if (!response.ok) throw new Error('Falha ao buscar dados.');
                return response.json();
            })
            .then(data => {
                if (historyType === 'route_history') {
                    buildRouteHistory(panel, data);
                }
            })
            .catch(error => {
                console.error('Erro ao buscar histórico:', error);
                panel.innerHTML = '<p style="color: red;">Erro ao carregar o histórico. Tente novamente.</p>';
            });
    }

    const driverTableBody = document.querySelector('.driver-table tbody');
    if (driverTableBody) {
        driverTableBody.addEventListener('click', function (event) {
            const target = event.target.closest('a.action-link');
            if (!target) return;

            event.preventDefault();
            const row = target.closest('tr');
            const pk = row.dataset.pk;

            if (target.classList.contains('action-view') && detailsModal) {
                event.preventDefault();
                detailsModal.dataset.currentPk = pk;

                document.getElementById('tab-panel-routes').innerHTML = '<p class="history-loading">Carregando histórico...</p>';
                detailsModal.querySelectorAll('.modal-tab-panel').forEach(p => p.style.display = 'none');
                detailsModal.querySelector('#tab-panel-details').style.display = 'block';
                detailsModal.querySelectorAll('.modal-tab-link').forEach(t => t.classList.remove('active'));
                detailsModal.querySelector('.modal-tab-link[data-target="tab-panel-details"]').classList.add('active');

                const driverName = row.dataset.full_name;
                detailsModal.querySelector('#details-driver-name').textContent = driverName;
                detailsModal.querySelector('#details-driver-id').textContent = `ID: D${pk.padStart(4, '0')}`;

                const statusTag = detailsModal.querySelector('#details-status-tag');
                const isActive = row.dataset.is_active === 'True';

                if (isActive) {
                    statusTag.textContent = '✓ Ativo';
                    statusTag.className = 'status-tag-driver status-active';
                } else {
                    statusTag.textContent = '✗ Suspenso';
                    statusTag.className = 'status-tag-driver status-suspended';
                }

                detailsModal.querySelector('#details-full-name').textContent = driverName;
                detailsModal.querySelector('#details-email').textContent = row.dataset.email;
                
                const licenseEl = detailsModal.querySelector('#details-license-number');
                licenseEl.textContent = formatCNH(row.dataset.license_number);

                const admDate = row.dataset.admission_date;
                try {
                    detailsModal.querySelector('#details-admission-date').textContent = new Date(admDate + 'T00:00:00').toLocaleDateString('pt-BR');
                } catch (e) {
                    detailsModal.querySelector('#details-admission-date').textContent = 'Data inválida';
                }

                const demissionItem = detailsModal.querySelector('#details-demission-item');
                const demissionDateEl = detailsModal.querySelector('#details-demission-date');
                const demissionDate = row.dataset.demission_date;

                if (!isActive && demissionDate) {
                    try {
                        demissionDateEl.textContent = new Date(demissionDate + 'T00:00:00').toLocaleDateString('pt-BR');
                        demissionItem.style.display = 'block';
                    } catch (e) {
                        demissionDateEl.textContent = 'Data inválida';
                        demissionItem.style.display = 'block';
                    }
                } else {
                    demissionItem.style.display = 'none';
                    demissionDateEl.textContent = '';
                }

                detailsModal.classList.add('active');
            }

            if (target.classList.contains('action-edit')) {
                addDriverModal.querySelector('#driver-modal-title').textContent = 'Editar Motorista';

                document.getElementById('id_full_name').value = row.dataset.full_name;
                document.getElementById('id_email').value = row.dataset.email;
                
                const cnhField = document.getElementById('id_license_number');
                cnhField.value = formatCNH(row.dataset.license_number);
                
                document.getElementById('id_admission_date').value = row.dataset.admission_date;

                driverForm.action = `/drivers/${pk}/update/`;
                addDriverModal.classList.add('active');
            }

            if (target.classList.contains('action-delete')) {
                demissionForm.action = `/drivers/${pk}/deactivate/`;
                demissionModal.classList.add('active');
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

            const driverPk = detailsModal.dataset.currentPk;
            if (targetPanelId === 'tab-panel-routes') {
                fetchHistory(driverPk, 'route_history', targetPanelId);
            }
        });
    }

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(button => {
            button.addEventListener('click', () => modal.classList.remove('active'));
        });
        modal.addEventListener('click', e => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});