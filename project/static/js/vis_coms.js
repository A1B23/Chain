collectCount = 0;
collect = false;

function collected(jsonIn, data) {
    var json = JSON.parse(jsonIn);
    if (json.hasOwnProperty("delayID")) {
        var typ = data[0];
        var from = data[1];
        var to = json.url;
        var pos = to.indexOf(":", 6);
        if (pos > 0) {
            var toDom = to.substring(0, pos + 5);
            comNodes.push({ 'iter': 0, 'fromType': typ, 'fromDom': from, 'url': to, 'toType': getType(toDom), 'toDom': toDom, 'delayID': json.delayID });
        }
    }
    drawCanvas();
}

function drawAllComs() {
    var lenc = comNodes.length;
    for (var com = 0; com < lenc; com++) {
        var item = comNodes[com];
        if (item.hasOwnProperty('delta')) {
            var show = item.url.substring(item.url.indexOf("/", 8) + 1);
            var node = item.delta;
            var gr = ctx.createRadialGradient(node.x, node.y, node.size / 4, node.x, node.y, node.size);
            var cols = ['rgb(0,0,255)', 'rgb(0,255,255)', 'rgb(0,0,0)'];
            if (animCol.hasOwnProperty(show)) {
                cols = animCol[show];
            }
            gr.addColorStop(0, cols[0]);
            gr.addColorStop(0.5, cols[1]);
            gr.addColorStop(1, cols[2]);
            ctx.fillStyle = gr;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2, false);
            ctx.closePath();
            ctx.fill();
            ctx.fillStyle = "black";
            ctx.font = "10px _sans";
            ctx.textBaseline = "top";
            var use_y = node.y;
            ctx.fillText(show, node.x, node.y + (node.toRight ? -node.size * 2 : node.size));
        }
    }
}

function collectRegex(regex) {
    $("#csusp").prop("disabled", false);
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                if (nodes[typ].hasOwnProperty(dom)) {
                    doPOSTSynch(dom + "/visualCfg", { 'active': true, 'pattern': regex });
                }
            }
        }
    }
}

function collectSuspend() {
    if ($("#crun").text() != "run") {
        collectPause();
    }
    $("#csusp").prop("disabled", true);
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                if (nodes[typ].hasOwnProperty(dom)) {
                    doPOSTSynch(dom + "/visualCfg",  { 'active': false, 'pattern': "" });
                }
            }
        }
    }
}

function doCollect(contin) {
    if (collectCount <= 0) {
        for (var typ in nodes) {
            if (nodes.hasOwnProperty(typ)) {
                for (var dom in nodes[typ]) {
                    if (nodes[typ].hasOwnProperty(dom)) {
                        collectCount++;
                        doGETCallback(dom + "/visualGet", collected, [typ, dom]);
                    }
                }
            }
        }
    }
    if ((collect == true) && contin) {
        var tim = +$("#refreshRate").val();
        setTimeout(function () { doCollect(true); }, tim);
    }

}

function collectRun() {
    if ($("#crun").text() == "run") {
        $("#crun").text("stop");
        collect = true;
        $("#cstep").prop("disabled", true);
        $("#cpause").prop("disabled", false);
        setTimeout(function () { doCollect(true); }, 100)
    } else {
        collectPause();
    }
}

function collectPause() {
    collect = false;
    $("#crun").text("run");
    $("#cstep").prop("disabled", false);
    $("#cpause").prop("disabled", true);
}

function collectStep() {
    collect = false;
    doCollect(false);
}

setTimeout(function () { updateCom() }, 100);

function releaseFor(url) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            // we ignore reply for now, but maybe can make use of reply for animation....
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function updateCom() {
    var comNodesL = comNodes.length;
    if (comNodesL > 0) {
        for (var com = 0; com < comNodesL; com++) {
            var item = comNodes[com];
            if (item.iter >= maxIter) {
                comNodes.splice(com, 1);
                com--;
                comNodesL--;
                releaseFor(item.fromDom + "/visualRelease/" + item.delayID);
                continue;
            }
            var from = getXYType(item.fromType, item.fromDom)
            if (from.hasOwnProperty(item.toDom)) {
                var to = getXYType(item.toType, item.toDom);
                var deltax = (to.x - from.x) / maxIter * item.iter;
                var use_y = from.y;
                var use_x = from.x;
                var toright = true;
                if (to.x < from.x) {
                    use_y += 7;
                    use_x -= 7;
                    toright = false;
                } else {
                    use_y -= 9;
                    use_x += 9;
                }

                comNodes[com]['delta'] = { 'x': use_x + deltax, 'y': deltax * from[item.toDom].slope + use_y, 'size': 10, 'toRight': toright };
            } else {
                console.log("No to Dom for " + com + " "+item);
                console.log(from);
                comNodes[com]['delta'] = { 'x': from.x, 'y': from.y, 'size': 10 };
            }
        }
        if (collect) {
            drawCanvas();
        }
        for (var com = 0; com < comNodesL; com++) {
            comNodes[com].iter = comNodes[com].iter + 1;
        }
    }
    setTimeout(function () { updateCom() }, +$("#animDelay").val());
}

function doGETCallback(url, callBack, callBackData) {
    var port = 5555;
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            collectCount--;
            callBack(this.responseText, callBackData);
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function doPOSTSynch(url, data) {
    var port = 5555;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url, false);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send((typeof data == 'string') ? data : JSON.stringify(data));
    var json = { "message": "fail" };
    json = JSON.parse(xhr.responseText);
    return [json, xhr.status];
}
