console.log("script loaded")
// static/js/ckeditor_config.js

document.addEventListener('DOMContentLoaded', function () {
    CKEDITOR.on('instanceReady', function (evt) {
        var editor = evt.editor;
        //
        // editor.on('fileUploadResponse', function (evt) {
        //     var fileLoader = evt.data.fileLoader;
        //     var xhr = fileLoader.xhr;
        //     var data = JSON.parse(xhr.responseText);
        //
        //
        //     // Modify the URL to include the base URL
        //     if (data.url) {
        //         data.url = baseURL + data.url;
        //         console.log(data.url)
        //     }
        //
        //     console.log(data)
        //     xhr.responseText = JSON.stringify(data);
        // });

        editor.document.on('keydown', function (event) {
            // keyup event in ckeditor
            // console.log(event.data.$.code)
            if (event.data.$.code === 'Backspace' || event.data.$.code === 'Delete') {
                // console.log(event)
                // console.log(editor.document)
                // console.log(editor)
                // console.log(editor.getSelection().getSelectedElement())
                const selectedElement = editor.getSelection().getSelectedElement()
                if (selectedElement && selectedElement.is('img')) {
                    // Prevent default behavior
                    const selectedImageUrl = selectedElement.getAttribute('src');
                    console.log(selectedImageUrl)
                    deleteImage(selectedImageUrl)
                    // Rest of your deletion logic using selectedImageUrl
                }
            }
        });


    });

});


function deleteImage(url) {
    fetch('/ckeditor/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({file_path: url}),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                alert('Image deleted successfully!');
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch((error) => console.error('Fetch error: ', error)); // Log fetch errors

}

// Helper function to get the CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}