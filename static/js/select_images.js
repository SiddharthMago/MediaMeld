$(document).ready(function() {
    var selected_images = [];
    $('.li-image').click(function() {
        $(this).children('i').toggleClass('selected');
        img_text = $(this).children('li').children('img').attr('src');
        if (selected_images.includes(img_text)) {
            selected_images.splice(selected_images.indexOf(img_text), 1);
        }
        else {
            selected_images.push(img_text);
        }
        console.log(selected_images);
    });

    $('.video-button').click(function() {
        $.ajax({
            url: '/recieve_images',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ images: selected_images }),
            success: function(response) {
                // Handle the response from the server
                console.log(response);
                $(location).prop('href', '/select_audio');
            },
            error: function(error) {
                // Handle any errors
                console.log(error);
            }
        });
        
    });
});