$(document).ready(() => {
    // Get the base URL
    var baseUrl = window.location.origin;
    $('#test').click(() => {
        console.log("hi")
        window.location.href = location.href + "click";
    });
    $('#add_workflow').click(() => {
        console.log("hii")
        window.location.href = baseUrl + "/workflows/add";
    });

    $('#submit_prompt').click(() => {
        var prompt = $("#prompt").val();
        var csrfToken = $('meta[name=csrf-token]').attr('content');
        var data = { "prompt": prompt }
        console.log(prompt)
        $.ajax({
            url: '/workflows/openai', // Replace with your API endpoint
            method: 'POST',
            contentType: "application/json",
            data: JSON.stringify(data),
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function (data) {
                console.log(data)
                // Handle the successful response here
                var html = "<img src=" + data.url + " alt=Description of the image></img>"
                $('.container-res').html(html);
            },
            error: function (error) {
                // Handle errors here
                console.log('Error:', error);
            }
        });
    });
});