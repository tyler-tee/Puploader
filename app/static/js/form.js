var form = document.getElementById("formNewFolder");
form.addEventListener("submit", onSubmitForm);

function onSubmitForm(e) {
    e.preventDefault();
    $('#formModal').modal('hide');
    $('#btnNewForm').hide();
    $('#message').show();
}