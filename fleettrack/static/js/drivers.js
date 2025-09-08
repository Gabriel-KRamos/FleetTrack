// static/js/drivers.js (VERSÃO FINAL E DINÂMICA)
document.addEventListener('DOMContentLoaded', function() {
    flatpickr(".datepicker", { dateFormat: "d/m/Y", locale: "pt" });

    const addDriverModal = document.getElementById('add-driver-modal');
    const driverForm = document.getElementById('driver-form');
    const driverModalTitle = document.getElementById('driver-modal-title');

    // Abre o modal para ADICIONAR
    document.getElementById('open-add-driver-modal').addEventListener('click', () => {
        driverForm.reset();
        driverModalTitle.textContent = 'Adicionar Novo Motorista';
        // A senha deve ser opcional na edição, então mostramos o campo
        document.getElementById('id_password').parentElement.style.display = 'block';
        driverForm.action = `/accounts/drivers/add/`;
        addDriverModal.classList.add('active');
    });

    // Delegação de eventos para a tabela
    document.querySelector('.driver-table tbody').addEventListener('click', function(event) {
        const target = event.target.closest('a');
        if (!target) return;

        const row = target.closest('tr');
        const pk = row.dataset.pk;

        // Botão EDITAR
        if (target.classList.contains('action-edit')) {
            event.preventDefault();
            driverModalTitle.textContent = 'Editar Motorista';

            // Preenche o formulário com data-attributes da linha
            document.getElementById('id_full_name').value = row.dataset.full_name;
            document.getElementById('id_email').value = row.dataset.email;
            document.getElementById('id_phone_number').value = row.dataset.phone;
            document.getElementById('id_license_number').value = row.dataset.license;

            // Esconde o campo de senha na edição
            document.getElementById('id_password').parentElement.style.display = 'none';

            driverForm.action = `/accounts/drivers/${pk}/update/`;
            addDriverModal.classList.add('active');
        }

        // Botão DESATIVAR
        if (target.classList.contains('action-delete')) {
            event.preventDefault();
            const demissionModal = document.getElementById('demission-modal');
            const demissionForm = document.getElementById('demission-form');
            demissionForm.action = `/accounts/drivers/${pk}/deactivate/`;
            demissionModal.classList.add('active');
        }
    });

    // Lógica para fechar modais
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', e => {
            if (e.target === modal || e.target.classList.contains('close-modal')) {
                modal.classList.remove('active');
            }
        });
    });
});