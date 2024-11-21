let form = document.getElementById("formNewFolder");
form.addEventListener("submit", onSubmitForm);

function onSubmitForm(e) {
    e.preventDefault();
    $('#formModal').modal('hide');
    $('#btnNewForm').hide();
    $('#message').show();
}

function handleKeyDown(event) {
    console.log('Key down:', event.key);
}

function handleKeyPress(event) {
    console.log('Key press:', event.key);
}

function handleKeyUp(event) {
    console.log('Key up:', event.key);
}
