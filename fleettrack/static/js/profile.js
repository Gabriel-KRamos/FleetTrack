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
            const errorLists = passwordForm.querySelectorAll('.errorlist'); // Busca erros dentro do form de senha
            errorLists.forEach(list => list.innerHTML = '');
        });
    }

    const passwordFormHasErrors = document.body.dataset.showPasswordErrors === 'true';
    if (passwordFormHasErrors && passwordForm) {
         passwordForm.style.display = 'block';
         profileLayout.classList.add('password-edit-mode');
    }
});