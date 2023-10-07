var api_path = window.location.pathname;
var api_pathSearch = window.location.search;
var api_load = false;
var api_CSRFToken = null;
var alertTimer;

$(document).ready(function () {
    if (api_path == "/") {
        api_path = `/dashboard`;
    }

    api_loadWidget(api_path + api_pathSearch);

    $(document).on("click", ".alert .close", function (event) {
        $(".alert").fadeOut(300, function() {
            $(this).remove();
        });
        event.stopPropagation();
    });

    $(window).on("popstate", function () {
        var path = window.location.pathname;
        if (!api_load) {
            api_setWidget({ url: `widget${path}` });
        } else {
            api_pathSearch = window.location.search;
            history.pushState(null, null, api_path + api_pathSearch);
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
            if (path != "javascript:;" && !path.startsWith("#") && path != api_path) {
                if (!api_load) {
                    api_loadWidget(path);
                }
            }
        }
    });
});

function api_isValidURL(url) {
    try {
        new URL(url);
        return true;
    } catch (error) {
        return false;
    }
}

function api_getCSRFToken(callback) {
    $.ajax({
        url: `/api/web/token/csrf`,
        type: "GET",
        dataType: "json",
        success: function (xhr) {
            if (xhr.success) {
                api_CSRFToken = xhr.token;
                callback(api_CSRFToken);
            } else {
                api_CSRFToken = null;
                callback(api_CSRFToken);
            }
        },
        error: function (xhr) {
            api_CSRFToken = null;
            callback(api_CSRFToken);
        }
    });
}

function api_loadWidget(path) {
    if (!api_load) {
        api_path = path;
        history.pushState(null, null, api_path);
        api_setWidget({});
    }
}

function api_setWidget({id = "#content", url = `widget${api_path}`, type = "GET"}) {
    if (!api_load) {
        api_classActive();
        
        api_load = true;
        $("html, body").animate({ scrollTop: 0 }, "slow");

        $(id).fadeOut(100, function () {
            $(this).html($("#preolader-content").html()).fadeIn(400);
        });

        var response = api_sendData({url: url, type: type});
        setTimeout(function(){
            response.then(function (response) {                
                $(id).fadeOut(400, function () {
                    $(this).html(response.html).fadeIn(400);
                });
                api_load = false;                
            }).catch(function (response) {
                $(id).fadeOut(400, function () {
                    $(this).html(response.responseJSON.html).fadeIn(400);
                });
                api_load = false;
            });
        }, 1000);
    }
}

function api_sendData({url = "", type = "POST", formData = new FormData()}) {
    return new Promise(function (resolve, reject) {
        api_getCSRFToken(function (token) {
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
                        xhr.setRequestHeader("X-CSRFToken", api_CSRFToken);
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

function api_loadloader(element, html, delement, disabled, timeOut, timeIn){
    element.fadeOut(timeOut, function () {
        $(this).html(html).fadeIn(timeIn);
    });
    delement.attr("disabled", disabled);
}

function api_alert({type = "danger", title = "¡Ocurrió un error!", text = ""}){
    $(".alert").remove();  
    clearTimeout(alertTimer);
    alertTimer = setTimeout(function(){
        $(".alert").remove();  
    }, 5000);  
    return `<div class="alert alert-${type}"><div class="body"><span>${title}</span> ${text}</div><div class="close"><i class="fa-solid fa-xmark"></i></div></div>`;
}

function api_classActive(){
    api_path = window.location.pathname;

    $(".menu li a").each(function() {
        var url = $(this).attr("href");
        var liElement = $(this).parent();

        if (url === api_path) {
            liElement.addClass("active");
        } else {
            liElement.removeClass("active");
        }
    });      
}

function api_dataTable(id, action, columns){
    var table = $(id).DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: "/api/web/data/table",
            type: "POST",
            data: function (d) {
                d.start = d.start || 0;
                d.length = d.length;
                d.action = action;
                d.search = d.search.value || "";
                d.order_column = d.columns[d.order[0].column].data;
                d.order_direction = d.order[0].dir;
            },
            beforeSend: function (xhr, settings) {
                if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                    xhr.setRequestHeader("X-CSRFToken", api_CSRFToken);
                }
            }
        },
        columns: columns,
        searching: true,
        ordering: true
    });

    return table;
}