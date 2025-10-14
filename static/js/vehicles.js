document.addEventListener('DOMContentLoaded', function() {
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    const addVehicleModal = document.getElementById('add-vehicle-modal');
    const deactivateModal = document.getElementById('deactivate-vehicle-modal');
    const detailsModal = document.getElementById('vehicle-details-modal');

    const vehicleForm = document.getElementById('vehicle-form');
    const deactivateForm = document.getElementById('deactivate-form');

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
        vehicleTableBody.addEventListener('click', function(event) {
            const target = event.target.closest('a');
            if (!target) return;

            const row = target.closest('tr');
            const pk = row.dataset.pk;

            if (target.classList.contains('action-view') && detailsModal) {
                event.preventDefault();
                detailsModal.querySelector('#details-plate').textContent = row.dataset.plate;
                detailsModal.querySelector('#details-model-year').textContent = `${row.dataset.model} (${row.dataset.year})`;
                const statusTag = detailsModal.querySelector('#details-status-tag');
                statusTag.textContent = row.dataset.status_display;
                statusTag.className = `status-tag status-${row.dataset.status}`;
                detailsModal.querySelector('#details-model').textContent = row.dataset.model;
                detailsModal.querySelector('#details-year').textContent = row.dataset.year;
                detailsModal.querySelector('#details-mileage').textContent = `${row.dataset.mileage} km`;
                const acqDate = row.dataset.acquisition_date;
                detailsModal.querySelector('#details-acquisition-date').textContent = new Date(acqDate).toLocaleDateString('pt-BR', { timeZone: 'UTC' });
                detailsModal.querySelector('#details-driver-name').textContent = row.dataset.driver_name;
                detailsModal.classList.add('active');
            }

            if (target.classList.contains('action-edit') && addVehicleModal) {
                event.preventDefault();
                addVehicleModal.querySelector('#vehicle-modal-title').textContent = 'Editar Veículo';
                addVehicleModal.querySelector('#vehicle-submit-button').textContent = 'Salvar Alterações';
                document.querySelector('#add-vehicle-modal #id_plate').value = row.dataset.plate;
                document.querySelector('#add-vehicle-modal #id_model').value = row.dataset.model;
                document.querySelector('#add-vehicle-modal #id_year').value = row.dataset.year;
                document.querySelector('#add-vehicle-modal #id_acquisition_date').value = row.dataset.acquisition_date;
                document.querySelector('#add-vehicle-modal #id_mileage').value = row.dataset.mileage;
                document.querySelector('#add-vehicle-modal #id_status').value = row.dataset.status;
                if (vehicleForm) vehicleForm.action = `/vehicles/${pk}/update/`;
                addVehicleModal.classList.add('active');
            }

            if (target.classList.contains('action-delete') && deactivateModal) {
                event.preventDefault();
                if (deactivateForm) deactivateForm.action = `/vehicles/${pk}/deactivate/`;
                deactivateModal.classList.add('active');
            }
        });
    }

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(button => button.addEventListener('click', () => modal.classList.remove('active')));
        modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });
    });
});