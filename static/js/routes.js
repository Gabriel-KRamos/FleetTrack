document.addEventListener('DOMContentLoaded', function() {
    console.log("routes.js: Script carregado e DOM pronto.");

    // Inicializa o seletor de data e hora
    try {
        flatpickr(".datetimepicker", {
            enableTime: true,
            dateFormat: "d/m/Y H:i",
            time_24hr: true,
            locale: "pt"
        });
        console.log("routes.js: Flatpickr inicializado.");
    } catch(e) {
        console.error("routes.js: Erro ao inicializar o Flatpickr.", e);
    }

    // Referências aos elementos do DOM
    const routeModal = document.getElementById('route-modal');
    const cancelModal = document.getElementById('cancel-route-modal');
    const routeForm = document.getElementById('route-form');
    const cancelForm = document.getElementById('cancel-form');
    const modalTitle = document.getElementById('route-modal-title');
    const openAddRouteBtn = document.getElementById('open-add-route-modal');
    const routeGrid = document.querySelector('.route-cards-grid');

    if (!routeModal || !cancelModal || !routeForm || !cancelForm) {
        console.error("routes.js: Um ou mais modais/formulários não foram encontrados. Verifique os IDs no HTML.");
        return;
    }

    // 1. Abrir modal para ADICIONAR uma nova rota
    if (openAddRouteBtn) {
        openAddRouteBtn.addEventListener('click', () => {
            console.log("routes.js: Botão 'Adicionar Rota' clicado.");
            routeForm.reset();
            routeForm.action = `/routes/add/`;
            modalTitle.textContent = 'Adicionar Nova Rota';
            routeModal.classList.add('active');
        });
    } else {
        console.warn("routes.js: Botão 'open-add-route-modal' não encontrado.");
    }

    // 2. Lidar com cliques nos botões dos cards (EDITAR e CANCELAR)
    if (routeGrid) {
        console.log("routes.js: Event listener adicionado ao grid de rotas.");
        routeGrid.addEventListener('click', function(event) {
            const button = event.target.closest('button');
            if (!button) return;

            const card = button.closest('.route-card');
            if (!card) return;
            
            const pk = card.dataset.pk;

            if (button.classList.contains('action-edit')) {
                console.log(`routes.js: Botão EDITAR clicado para a rota PK=${pk}.`);
                
                // --- INÍCIO DA CORREÇÃO ---
                const startTimeInput = document.getElementById('id_start_time');
                const endTimeInput = document.getElementById('id_end_time');

                document.getElementById('id_start_location').value = card.dataset.start_location;
                document.getElementById('id_end_location').value = card.dataset.end_location;
                document.getElementById('id_vehicle').value = card.dataset.vehicle_id;
                document.getElementById('id_driver').value = card.dataset.driver_id;
                
                // Forma correta de acessar a instância do flatpickr
                if (startTimeInput && startTimeInput._flatpickr) {
                    startTimeInput._flatpickr.setDate(card.dataset.start_time, true, "d/m/Y H:i");
                }
                if (endTimeInput && endTimeInput._flatpickr) {
                    endTimeInput._flatpickr.setDate(card.dataset.end_time, true, "d/m/Y H:i");
                }
                // --- FIM DA CORREÇÃO ---
                
                routeForm.action = `/routes/${pk}/update/`;
                modalTitle.textContent = 'Editar Rota';
                routeModal.classList.add('active');
            }

            if (button.classList.contains('action-cancel')) {
                console.log(`routes.js: Botão CANCELAR clicado para a rota PK=${pk}.`);
                if (button.disabled) {
                    console.log("routes.js: O botão de cancelar está desabilitado e não pode ser acionado.");
                    return;
                }
                cancelForm.action = `/routes/${pk}/cancel/`;
                cancelModal.classList.add('active');
            }
        });
    } else {
        console.warn("routes.js: Grid de rotas '.route-cards-grid' não encontrado.");
    }

    // 3. Lógica genérica para fechar QUALQUER modal
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