$(document).ready(function() {
    if (localStorage.getItem("darkMode") === "enabled") {
        $("body").addClass("bg-dark text-white");
        $("#dark-mode-toggle").text("Light Mode");
    }

    function toggleDarkMode() {
        $("body").toggleClass("bg-dark text-white");
        if ($("body").hasClass("bg-dark")) {
            localStorage.setItem("darkMode", "enabled");
            $("#dark-mode-toggle").text("Light Mode");
        } else {
            localStorage.setItem("darkMode", "disabled");
            $("#dark-mode-toggle").text("Dark Mode");
        }
    }

    $("#dark-mode-toggle").click(toggleDarkMode);

    function updateImage(timestamp) {
        $("#pdf-image").attr("src", "/show_page?t=" + timestamp);
    }

    function getRandomPage() {
        $.post("/random_page", function(data) {
            if (data.page_num) {
                updateImage(data.timestamp);
                $("#page-info").text(`Page ${data.page_num} of ${data.total_pages}`);
                $("#prev-page-button").prop("disabled", data.page_num === 1);
                $("#next-page-button").prop("disabled", data.page_num === data.total_pages);
            }
        });
    }

    function navigatePage(direction) {
        $.ajax({
            type: "POST",
            url: "/navigate_page",
            contentType: "application/json",
            data: JSON.stringify({ direction: direction }),
            success: function(data) {
                if (data.page_num) {
                    updateImage(data.timestamp);
                    $("#page-info").text(`Page ${data.page_num} of ${data.total_pages}`);
                    $("#prev-page-button").prop("disabled", data.page_num === 1);
                    $("#next-page-button").prop("disabled", data.page_num === data.total_pages);
                }
            }
        });
    }

    $("#random-page-button").click(getRandomPage);
    $("#prev-page-button").click(function() { navigatePage("prev"); });
    $("#next-page-button").click(function() { navigatePage("next"); });

    $(document).keydown(function(event) {
        if (event.key === "ArrowLeft") {
            navigatePage("prev");
        } else if (event.key === "ArrowRight") {
            navigatePage("next");
        } else if (event.key === " " || event.key === "Enter") {
            getRandomPage();
        } else if (event.key.toLowerCase() === "l") {
            toggleDarkMode();
        }
    });
});
