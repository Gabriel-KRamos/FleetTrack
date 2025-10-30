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
    const cancelForm = document.getElementById('cancel-maintenance-form');

    const modalTitle = document.getElementById('maintenance-modal-title');
    const openAddBtn = document.getElementById('open-add-maintenance-modal');

    const vehicleSelect = document.getElementById('id_vehicle'); 
    const mileageDisplay = document.getElementById('mileage-display-value'); 
    const mileageInput = document.getElementById('id_current_mileage'); 

    const serviceChoiceSelect = document.getElementById('id_service_choice');
    const serviceTypeOtherWrapper = document.getElementById('service_type_other_wrapper');
    const serviceTypeOtherInput = document.getElementById('id_service_type_other');

    function toggleServiceTypeOther(show) {
        if (show) {
            serviceTypeOtherWrapper.style.display = 'block';
            serviceTypeOtherInput.required = true;
        } else {
            serviceTypeOtherWrapper.style.display = 'none';
            serviceTypeOtherInput.required = false;
            serviceTypeOtherInput.value = '';
        }
    }

    if (serviceChoiceSelect) {
        serviceChoiceSelect.addEventListener('change', function() {
            toggleServiceTypeOther(this.value === 'Outro');
        });
    }

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
            
            toggleServiceTypeOther(false);
            if (serviceChoiceSelect) {
                serviceChoiceSelect.value = '';
            }
            
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
            
            if (serviceChoiceSelect) {
                const serviceTypeData = row.dataset.service_type;
                const predefinedChoices = Array.from(serviceChoiceSelect.options).map(opt => opt.value);
    
                if (predefinedChoices.includes(serviceTypeData)) {
                    serviceChoiceSelect.value = serviceTypeData;
                    toggleServiceTypeOther(false);
                } else {
                    serviceChoiceSelect.value = 'Outro';
                    serviceTypeOtherInput.value = serviceTypeData;
                    toggleServiceTypeOther(true);
                }
            }
            
            document.querySelector('#maintenance-modal #id_mechanic_shop_name').value = row.dataset.mechanic_shop_name;
            document.querySelector('#maintenance-modal #id_estimated_cost').value = row.dataset.estimated_cost;
            
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
            if (cancelForm) {
                cancelForm.action = `/maintenance/${pk}/cancel/`;
                cancelModal.classList.add('active');
            } else {
                console.error("Elemento com ID 'cancel-maintenance-form' não encontrado.");
            }
        }

        if (target.classList.contains('action-complete')) {
            document.querySelector('#complete-maintenance-modal #id_actual_cost').value = row.dataset.estimated_cost;
            const endDateInput = document.querySelector('#complete-maintenance-modal #id_actual_end_date');
            if (endDateInput._flatpickr) {
                endDateInput._flatpickr.setDate(row.dataset.end_date, true, "d/m/Y H:i");
            }
            if (completeForm) {
                completeForm.action = `/maintenance/${pk}/complete/`;
                completeModal.classList.add('active');
            } else {
                console.error("Elemento com ID 'complete-maintenance-form' não encontrado.");
            }
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