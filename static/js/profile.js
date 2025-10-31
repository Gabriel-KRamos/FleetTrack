document.addEventListener('DOMContentLoaded', function() {
    const profileLayout = document.querySelector('.profile-layout');
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const saveChangesBtn = document.getElementById('save-changes-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const profileForm = document.getElementById('profile-form'); 

    const changePasswordBtn = document.getElementById('change-password-btn');
    const passwordForm = document.getElementById('password-form');
    const cancelPasswordBtn = document.getElementById('cancel-password-change-btn');
    const updatePasswordBtn = document.getElementById('update-password-btn');
    const passwordFormFields = passwordForm ? passwordForm.querySelectorAll('input[type="password"]') : [];

    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', function(e) {
            e.preventDefault();
            profileLayout.classList.add('edit-mode');
            if (passwordForm && passwordForm.style.display !== 'none') {
                passwordForm.style.display = 'none';
                profileLayout.classList.remove('password-edit-mode');
                passwordFormFields.forEach(input => input.value = '');
            }
        });
    }

    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function(e) {
            e.preventDefault();
            profileLayout.classList.remove('edit-mode');
             if (profileForm) profileForm.reset();
        });
    }

     if (changePasswordBtn && passwordForm) {
        changePasswordBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!profileLayout.classList.contains('edit-mode')) {
                passwordForm.style.display = 'block';
                profileLayout.classList.add('password-edit-mode');
            } else {
                alert("Salve ou cancele a edição do perfil antes de alterar a senha.");
            }
        });
    }

    if (cancelPasswordBtn && passwordForm) {
        cancelPasswordBtn.addEventListener('click', function(e) {
            e.preventDefault();
            passwordForm.style.display = 'none';
            profileLayout.classList.remove('password-edit-mode');
            passwordFormFields.forEach(input => input.value = '');
            const errorLists = passwordForm.querySelectorAll('.errorlist'); 
            errorLists.forEach(list => list.innerHTML = '');
        });
    }

    const passwordFormHasErrors = document.body.dataset.showPasswordErrors === 'true';
    if (passwordFormHasErrors && passwordForm) {
         passwordForm.style.display = 'block';
         profileLayout.classList.add('password-edit-mode');
    }

    function formatCnpj(value) {
        if (!value) return '';
        let v = value.replace(/\D/g, '');
        if (v.length > 14) v = v.substring(0, 14);
        
        if (v.length > 12) {
            v = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
        } else if (v.length > 8) {
            v = v.replace(/^(\d{2})(\d{3})(\d{3})(\d{1,4})$/, '$1.$2.$3/$4');
        } else if (v.length > 5) {
            v = v.replace(/^(\d{2})(\d{3})(\d{1,3})$/, '$1.$2.$3');
        } else if (v.length > 2) {
            v = v.replace(/^(\d{2})(\d{1,3})$/, '$1.$2');
        }
        return v;
    }

    const cnpjDisplay = document.getElementById('display_cnpj');
    if (cnpjDisplay) {
        cnpjDisplay.textContent = formatCnpj(cnpjDisplay.textContent);
    }

    const cnpjInput = document.getElementById('id_cnpj');
    if (cnpjInput) {
        
        if (profileLayout.classList.contains('edit-mode')) {
             cnpjInput.value = formatCnpj(cnpjInput.value);
        }

        editProfileBtn.addEventListener('click', function() {
            cnpjInput.value = formatCnpj(cnpjInput.value);
        });

        cnpjInput.addEventListener('input', function (e) {
            e.target.value = formatCnpj(e.target.value);
        });
    }
});