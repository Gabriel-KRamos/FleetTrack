document.addEventListener('DOMContentLoaded', function() {
    flatpickr(".datetimepicker", {
        enableTime: true,
        dateFormat: "d/m/Y H:i",
        time_24hr: true,
        locale: "pt"
    });

    const maintenanceModal = document.getElementById('maintenance-modal');
    const completeModal = document.getElementById('complete-maintenance-modal');
    const cancelModal = document.getElementById('cancel-maintenance-modal');

    const maintenanceForm = document.getElementById('maintenance-form');
    const completeForm = document.getElementById('complete-maintenance-form');
    const cancelForm = document.getElementById('cancel-form');

    const modalTitle = document.getElementById('maintenance-modal-title');
    const openAddBtn = document.getElementById('open-add-maintenance-modal');

    const vehicleSelect = document.getElementById('id_vehicle'); 
    const mileageDisplay = document.getElementById('mileage-display-value'); 
    const mileageInput = document.getElementById('id_current_mileage'); 

    if (vehicleSelect) {
        vehicleSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const mileage = selectedOption.dataset.mileage;

            if (mileage) {
                mileageDisplay.textContent = `${mileage} km`; 
                mileageInput.value = mileage;
            } else {
                mileageDisplay.textContent = '-- selecione --'; 
                mileageInput.value = '';
            }
        });
    }

    if (openAddBtn) {
        openAddBtn.addEventListener('click', () => {
            maintenanceForm.reset();
            maintenanceForm.action = `/maintenance/add/`;
            modalTitle.textContent = 'Adicionar Nova Manutenção';
            
            vehicleSelect.value = ''; 
            mileageDisplay.textContent = '-- selecione --'; 
            mileageInput.value = ''; 
            
            maintenanceModal.classList.add('active');
        });
    }

    document.querySelector('.vehicle-table tbody').addEventListener('click', function(event) {
        const target = event.target.closest('a.action-link');
        if (!target) return;
        event.preventDefault();
        
        const row = target.closest('tr');
        const pk = row.dataset.pk;

        if (target.classList.contains('action-edit')) {
            modalTitle.textContent = 'Editar Manutenção';
            
            document.querySelector('#maintenance-modal #id_service_type').value = row.dataset.service_type;
            document.querySelector('#maintenance-modal #id_mechanic_shop_name').value = row.dataset.mechanic_shop_name;
            document.querySelector('#maintenance-modal #id_estimated_cost').value = row.dataset.estimated_cost;
            document.querySelector('#maintenance-modal #id_notes').value = row.dataset.notes;
            
            const currentMileage = row.dataset.current_mileage;
            vehicleSelect.value = row.dataset.vehicle_id; 
            mileageDisplay.textContent = `${currentMileage} km`; 
            mileageInput.value = currentMileage; 

            const startDateInput = document.querySelector('#maintenance-modal #id_start_date');
            if (startDateInput._flatpickr) {
                startDateInput._flatpickr.setDate(row.dataset.start_date, true, "d/m/Y H:i");
            }
            const endDateInput = document.querySelector('#maintenance-modal #id_end_date');
            if (endDateInput._flatpickr) {
                endDateInput._flatpickr.setDate(row.dataset.end_date, true, "d/m/Y H:i");
            }
            
            maintenanceForm.action = `/maintenance/${pk}/update/`;
            maintenanceModal.classList.add('active');
        }

        if (target.classList.contains('action-cancel')) {
            cancelForm.action = `/maintenance/${pk}/cancel/`;
            cancelModal.classList.add('active');
        }

        if (target.classList.contains('action-complete')) {
            document.querySelector('#complete-maintenance-modal #id_actual_cost').value = row.dataset.estimated_cost;
            const endDateInput = document.querySelector('#complete-maintenance-modal #id_actual_end_date');
            if (endDateInput._flatpickr) {
                endDateInput._flatpickr.setDate(row.dataset.end_date, true, "d/m/Y H:i");
            }
            completeForm.action = `/maintenance/${pk}/complete/`;
            completeModal.classList.add('active');
        }
    });

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