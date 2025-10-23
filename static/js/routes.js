document.addEventListener('DOMContentLoaded', function() {

    try {
        flatpickr(".datetimepicker", {
            enableTime: true,
            dateFormat: "d/m/Y H:i",
            time_24hr: true,
            locale: "pt"
        });
    } catch(e) { console.error("routes.js: Erro ao inicializar o Flatpickr.", e); }

    const routeModal = document.getElementById('route-modal');
    const cancelModal = document.getElementById('cancel-route-modal');
    const completeModal = document.getElementById('complete-route-modal');
    const summaryModal = document.getElementById('route-summary-modal');

    const routeForm = document.getElementById('route-form');
    const cancelForm = document.getElementById('cancel-form');
    const completeForm = document.getElementById('complete-route-form');
    
    const modalTitle = document.getElementById('route-modal-title');
    const openAddRouteBtn = document.getElementById('open-add-route-modal');
    const routeGrid = document.querySelector('.route-cards-grid');
    
    const errorDisplay = document.getElementById('form-modal-errors');

    if (!routeModal || !cancelModal || !routeForm || !cancelForm || !completeModal || !completeForm) {
        console.error("routes.js: Um ou mais modais/formulários não foram encontrados. Verifique os IDs no HTML.");
        return;
    }


    function displayErrorsInModal(errors) {
        let errorHtml = '<ul>';
        for (const field in errors) {
            errors[field].forEach(error => {
                errorHtml += `<li>${error.message || error}</li>`;
            });
        }
        errorHtml += '</ul>';
        
        errorDisplay.innerHTML = errorHtml;
        errorDisplay.style.display = 'block';
    }


    function clearErrorsInModal() {
        errorDisplay.innerHTML = '';
        errorDisplay.style.display = 'none';
    }

    routeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        clearErrorsInModal();
        
        const saveButton = document.getElementById('save-route-button');
        saveButton.textContent = 'Salvando...';
        saveButton.disabled = true;

        const formData = new FormData(routeForm);
        const actionUrl = routeForm.action;
        const csrfToken = formData.get('csrfmiddlewaretoken');

        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 200 && body.success) {
                routeModal.classList.remove('active');
                
                const summary = body.summary;

                const formatBRL = (value) => {
                    return (parseFloat(value) || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                };
                const formatNum = (value) => {
                     return (parseFloat(value) || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                };

                document.getElementById('summary-route-title').textContent = `${summary.start_location} → ${summary.end_location}`;
                document.getElementById('summary-distance').textContent = `${formatNum(summary.distance)} km`;
                document.getElementById('summary-toll-cost').textContent = formatBRL(summary.toll_cost);
                document.getElementById('summary-fuel-cost').textContent = formatBRL(summary.fuel_cost);
                
                if (summaryModal) {
                    summaryModal.classList.add('active');
                } else {
                    window.location.reload();
                }
            } else if (status === 400 && !body.success) {
                displayErrorsInModal(body.errors);
            } else {
                displayErrorsInModal({'__all__': ['Ocorreu um erro inesperado.']});
            }
        })
        .catch(error => {
            console.error('Erro no fetch:', error);
            displayErrorsInModal({'__all__': ['Erro de conexão. Tente novamente.']});
        })
        .finally(() => {
            saveButton.textContent = 'Salvar Rota';
            saveButton.disabled = false;
        });
    });

    if (openAddRouteBtn) {
        openAddRouteBtn.addEventListener('click', () => {
            routeForm.reset();
            clearErrorsInModal();
            routeForm.action = `/routes/add/`;
            modalTitle.textContent = 'Adicionar Nova Rota';
            routeModal.classList.add('active');
        });
    }

    if (routeGrid) {
        routeGrid.addEventListener('click', function(event) {
            const button = event.target.closest('button');
            if (!button) return;

            const card = button.closest('.route-card');
            if (!card) return;
            
            const pk = card.dataset.pk;


            if (button.classList.contains('action-edit')) {
                clearErrorsInModal();
                
                const startTimeInput = document.getElementById('id_start_time');
                const endTimeInput = document.getElementById('id_end_time');

                document.getElementById('id_start_location').value = card.dataset.start_location;
                document.getElementById('id_end_location').value = card.dataset.end_location;
                document.getElementById('id_vehicle').value = card.dataset.vehicle_id;
                document.getElementById('id_driver').value = card.dataset.driver_id;
                
                if (startTimeInput && startTimeInput._flatpickr) {
                    startTimeInput._flatpickr.setDate(card.dataset.start_time, true, "d/m/Y H:i");
                }
                if (endTimeInput && endTimeInput._flatpickr) {
                    endTimeInput._flatpickr.setDate(card.dataset.end_time, true, "d/m/Y H:i");
                }
                
                routeForm.action = `/routes/${pk}/update/`;
                modalTitle.textContent = 'Editar Rota';
                routeModal.classList.add('active');
            }

            if (button.classList.contains('action-cancel')) {
                if (button.disabled) return;
                
                cancelForm.action = `/routes/${pk}/cancel/`;
                cancelModal.classList.add('active');
            }


            if (button.classList.contains('action-complete')) {
                const estimatedDistance = card.dataset.estimated_distance || 0;
                document.getElementById('id_actual_distance').value = estimatedDistance.replace(',', '.');
                
                completeForm.action = `/routes/${pk}/complete/`;
                
                completeModal.classList.add('active');
            }
        });
    }

    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.querySelectorAll('.close-modal').forEach(button => {
            button.addEventListener('click', () => {
                modal.classList.remove('active');
                if (modal.id === 'route-summary-modal') {
                    window.location.reload();
                }
            });
        });
        modal.addEventListener('click', e => {
            if (e.target === modal) {
                modal.classList.remove('active');
                if (modal.id === 'route-summary-modal') {
                    window.location.reload();
                }
            }
        });
    });
});