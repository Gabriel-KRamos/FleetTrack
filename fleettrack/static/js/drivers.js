document.addEventListener('DOMContentLoaded', function() {
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    const addDriverModal = document.getElementById('add-driver-modal');
    const driverForm = document.getElementById('driver-form');
    const driverModalTitle = document.getElementById('driver-modal-title');
    
    document.getElementById('open-add-driver-modal').addEventListener('click', () => {
        driverForm.reset();
        driverModalTitle.textContent = 'Adicionar Novo Motorista';
        driverForm.action = `/drivers/add/`; // URL CORRETO
        addDriverModal.classList.add('active');
    });

    document.querySelector('.driver-table tbody').addEventListener('click', function(event) {
        const target = event.target.closest('a');
        if (!target) return;

        const row = target.closest('tr');
        const pk = row.dataset.pk;

        if (target.classList.contains('action-edit')) {
            event.preventDefault();
            driverModalTitle.textContent = 'Editar Motorista';
            
            addDriverModal.querySelector('#id_full_name').value = row.dataset.full_name;
            addDriverModal.querySelector('#id_email').value = row.dataset.email;
            addDriverModal.querySelector('#id_phone_number').value = row.dataset.phone_number;
            addDriverModal.querySelector('#id_license_number').value = row.dataset.license_number;
            addDriverModal.querySelector('#id_admission_date').value = row.dataset.admission_date;

            driverForm.action = `/drivers/${pk}/update/`; // URL CORRETO
            addDriverModal.classList.add('active');
        }

        if (target.classList.contains('action-delete')) {
            event.preventDefault();
            const demissionModal = document.getElementById('demission-modal');
            const demissionForm = document.getElementById('demission-form');
            demissionForm.action = `/drivers/${pk}/deactivate/`; // URL CORRETO
            demissionModal.classList.add('active');
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