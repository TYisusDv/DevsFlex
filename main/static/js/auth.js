var auth_path = window.location.pathname;
var auth_pathSearch = window.location.search;
var auth_load = false;
var auth_CSRFToken = null;

$(document).ready(function () {
    if (auth_path == "/auth" || auth_path == "/auth/") {
        auth_path = `/auth/sign-in${auth_pathSearch}`;
    }

    auth_loadWidget(auth_path);

    $(document).on("click", "#dark-mode", function (event) {
        $("body").toggleClass("theme-white theme-dark");
        var newTheme = $("body").hasClass("theme-white") ? "white" : "dark";
        $.cookie("theme", newTheme, { expires: 36500 });
        event.stopPropagation();
    });

    $(document).on("click", ".alert .close", function (event) {
        $(".alert").fadeOut(300, function() {
            $(this).remove();
        });
        event.stopPropagation();
    });

    $(window).on("popstate", function () {
        var path = window.location.pathname;
        if (!auth_load) {
            auth_setWidget({ url: `widget${path}` });
        } else {
            auth_pathSearch = window.location.search;
            history.pushState(null, null, auth_path + auth_pathSearch);
        }
    });

    $(document).on("click", "a", function (event) {
        event.preventDefault();

        var path = $(this).attr("href");
        var type = $(this).attr("type");

        if (type == "location") {
            window.location = path;
        } else if (type == "_blank") {
            window.open(path, "_blank");
        } else {
            if (path != "javascript:;" && !path.startsWith("#") && path != auth_path) {
                if (!auth_load) {
                    auth_loadWidget(path);
                }
            }
        }
    });
});

function auth_isValidURL(url) {
    try {
        new URL(url);
        return true;
    } catch (error) {
        return false;
    }
}

function auth_getCSRFToken(callback) {
    $.ajax({
        url: `/api/web/token/csrf`,
        type: "GET",
        dataType: "json",
        success: function (xhr) {
            if (xhr.success) {
                auth_CSRFToken = xhr.token;
                callback(auth_CSRFToken);
            } else {
                auth_CSRFToken = null;
                callback(auth_CSRFToken);
            }
        },
        error: function (xhr) {
            auth_CSRFToken = null;
            callback(auth_CSRFToken);
        }
    });
}

function auth_loadWidget(path) {
    if (!auth_load) {
        auth_path = path;
        auth_pathSearch = window.location.search;
        history.pushState(null, null, auth_path + auth_pathSearch);
        auth_setWidget({});
    }
}

function auth_setWidget({id = "#auth_content", url = `widget${auth_path}`, type = "GET"}) {
    if (!auth_load) {
        auth_load = true;
        $("html, body").animate({ scrollTop: 0 }, "slow");

        $(id).fadeOut(100, function () {
            $(this).html($("#main-preloader").html()).fadeIn(400);
        });

        var response = auth_sendData({url: url, type: type});
        setTimeout(function(){
            response.then(function (response) {                
                $(id).fadeOut(400, function () {
                    $(this).html(response.html).fadeIn(400);
                });
                auth_load = false;                
            }).catch(function (response) {
                auth_load = false;
            });
        }, 1000);
    }
}

function auth_sendData({url = "", type = "POST", formData = new FormData()}) {
    return new Promise(function (resolve, reject) {
        auth_getCSRFToken(function (token) {
            $.ajax({
                url: `/api/web/${url}`,
                type: type,
                data: formData,
                dataType: "json",
                processData: false,
                contentType: false,
                enctype: "multipart/form-data",
                beforeSend: function (xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                        xhr.setRequestHeader("X-CSRFToken", auth_CSRFToken);
                    }
                },
                success: function (xhr) {
                    resolve(xhr);
                },
                error: function (xhr) {
                    reject(xhr);
                }
            });
        });
    });
}

function auth_loadloader(element, html, delement, disabled, timeOut, timeIn){
    element.fadeOut(timeOut, function () {
        $(this).html(html).fadeIn(timeIn);
    });
    delement.attr("disabled", disabled);
}

function auth_alert({type = "danger", title = "¡Ocurrió un error!", text = ""}){
    $(".alert").remove();    
    return `<div class="alert alert-${type}"><div class="body"><span>${title}</span> ${text}</div><div class="close"><i class="fa-solid fa-xmark"></i></div></div>`;
}