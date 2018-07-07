cnt = 0;

$("#viewsizes").change(function () {
    setFramesHeight();
});

$("canvas").dblclick(function () {
    hideFrames();
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                var dx = getXYType(typ, dom);
                if ((dx.x - dx.size < globMousePos.x) && (dx.x + dx.size > globMousePos.x) &&
                    (dx.y - dx.size < globMousePos.y) && (dx.y + dx.size > globMousePos.y)) {
                    lastGUI = "#" + clearDom(dom);
                    $("#" + clearDom(dom)).show();
                    $("#GUI").prop("checked", true);
                    return;
                }
            }
        }
    }
});

$("#test").on("click", function () {
    ctx.save();
    setTimeout(function () { drawCom("W", "http://127.0.0.52:5555", "B", "http://127.0.0.2:5555", 0); }, 100);
});

$("#scan").on("change", function () {
    if (this.checked) {
        setTimeout(function () {
            if (initScan == false) {
                reScan();
            } else {
                newScan();
            }
        }, 100);
    }
});

$("#ctrl").on("change", function () {
    if (this.checked) {
        $("#views").show();
    } else {
        $("#views").hide();
    }
});

$("#GUI").on("change", function () {
    if (this.checked) {
        $(lastGUI).show();
    } else {
        hideFrames();
    }
});


// Additional GUI helper functions

function getWidth() {
    return $("#twidth")[0].value
}

function getHeight() {
    return $("#theight")[0].value
}

function getMousePos(canvas, evt) {
    var rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}

function hideFrames() {
    $(".iframes").each(function () {
        $(this).hide();
    });
    if (document.getElementById("ctrl").checked) {
        $("#views").show();
    } else {
        $("#views").hide();
    }
}

function setFramesHeight() {
    $(".iframes").each(function () {
        var h = $("#viewsizes").val() * 100;
        if (h == 0) {
            $(this).hide();
        } else {
            $(this).attr('height', h);
        }
    });
}


// helper function to show results as
function addLog(text, start) {
    if (start == true) {
        ntext = "\n---- [Command count:" + cnt + "]" + text
        cnt++
    } else {
        //ntext = "\n\r==> Reply:\n\r"+text
        ntext = text
    }
    //document.getElementById("response").value = document.getElementById("response").value + ntext;
    return ntext
}

function setShadow(on) {
    ctx.shadowColor = 'black';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetX = 5;
    ctx.shadowOffsetY = 5;
}


