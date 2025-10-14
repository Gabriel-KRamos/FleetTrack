document.addEventListener('DOMContentLoaded', function() {
    // Inicializa o seletor de data para o campo de admissão
    flatpickr(".datepicker", { dateFormat: "Y-m-d", locale: "pt" });

    // Referências aos modais e formulários
    const addDriverModal = document.getElementById('add-driver-modal');
    const demissionModal = document.getElementById('demission-modal');
    
    const driverForm = document.getElementById('driver-form');
    const demissionForm = document.getElementById('demission-form');
    
    // 1. Lógica para o botão "Adicionar Motorista"
    const openAddDriverBtn = document.getElementById('open-add-driver-modal');
    if (openAddDriverBtn && addDriverModal) {
        openAddDriverBtn.addEventListener('click', () => {
            driverForm.reset(); // Limpa o formulário
            addDriverModal.querySelector('#driver-modal-title').textContent = 'Adicionar Novo Motorista';
            driverForm.action = `/drivers/add/`; // Define a URL para criar um novo motorista
            addDriverModal.classList.add('active');
        });
    }

    // 2. Lógica para os botões "Editar" e "Demitir" na tabela
    const driverTableBody = document.querySelector('.driver-table tbody');
    if (driverTableBody) {
        driverTableBody.addEventListener('click', function(event) {
            const target = event.target.closest('a.action-link');
            if (!target) return;

            event.preventDefault();
            const row = target.closest('tr');
            const pk = row.dataset.pk;

            // Se o botão "Editar" for clicado
            if (target.classList.contains('action-edit')) {
                addDriverModal.querySelector('#driver-modal-title').textContent = 'Editar Motorista';
                
                // Preenche o formulário com os dados da linha da tabela
                document.getElementById('id_full_name').value = row.dataset.full_name;
                document.getElementById('id_email').value = row.dataset.email;
                document.getElementById('id_phone_number').value = row.dataset.phone_number;
                document.getElementById('id_license_number').value = row.dataset.license_number;
                document.getElementById('id_admission_date').value = row.dataset.admission_date;

                driverForm.action = `/drivers/${pk}/update/`; // Define a URL para atualizar
                addDriverModal.classList.add('active');
            }

            // Se o botão "Demitir" for clicado
            if (target.classList.contains('action-delete')) {
                demissionForm.action = `/drivers/${pk}/deactivate/`; // Define a URL para desativar
                demissionModal.classList.add('active');
            }
        });
    }

    // 3. Lógica genérica para fechar todos os modais
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        // Fechar ao clicar no 'X' ou no botão "Cancelar"
        modal.querySelectorAll('.close-modal').forEach(button => {
            button.addEventListener('click', () => modal.classList.remove('active'));
        });
        // Fechar ao clicar fora do conteúdo do modal
        modal.addEventListener('click', e => { 
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});