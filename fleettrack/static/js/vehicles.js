// static/js/vehicles.js (VERSÃO FINAL E DINÂMICA)
document.addEventListener('DOMContentLoaded', function() {
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    const addVehicleModal = document.getElementById('add-vehicle-modal');
    const vehicleForm = document.getElementById('vehicle-form');
    const vehicleModalTitle = document.getElementById('vehicle-modal-title');

    // Abre o modal para ADICIONAR
    document.getElementById('open-add-vehicle-modal').addEventListener('click', () => {
        vehicleForm.reset();
        vehicleModalTitle.textContent = 'Adicionar Novo Veículo';
        vehicleForm.action = `/vehicles/add/`;
        addVehicleModal.classList.add('active');
    });

    // Delegação de eventos para os botões de ação na tabela
    document.querySelector('.vehicle-table tbody').addEventListener('click', function(event) {
        const target = event.target.closest('a');
        if (!target) return;

        const row = target.closest('tr');
        const pk = row.dataset.pk;

        // Botão EDITAR
        if (target.classList.contains('action-edit')) {
            event.preventDefault();
            vehicleModalTitle.textContent = 'Editar Veículo';

            // Preenche o formulário com data-attributes da linha
            document.getElementById('id_plate').value = row.dataset.plate;
            document.getElementById('id_model').value = row.dataset.model;
            document.getElementById('id_year').value = row.dataset.year;
            document.getElementById('id_acquisition_date').value = row.dataset.acquisition_date;
            document.getElementById('id_status').value = row.dataset.status;

            vehicleForm.action = `/vehicles/${pk}/update/`;
            addVehicleModal.classList.add('active');
        }

        // Botão DESATIVAR
        if (target.classList.contains('action-delete')) {
            event.preventDefault();
            const deactivateModal = document.getElementById('deactivate-vehicle-modal');
            const deactivateForm = document.getElementById('deactivate-form');
            deactivateForm.action = `/vehicles/${pk}/deactivate/`;
            deactivateModal.classList.add('active');
        }
    });

    // Lógica genérica para fechar todos os modais
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', e => {
            if (e.target === modal || e.target.classList.contains('close-modal')) {
                modal.classList.remove('active');
            }
        });
    });
});