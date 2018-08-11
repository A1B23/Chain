collectCount = 0;
collect = false;

function collected(jsonIn, data) {
    var json = JSON.parse(jsonIn);
    nodes[data[0]][data[1]]['activePeers'] = json.activePeers
    nodes[data[0]][data[1]]['shareToPeers'] = json.shareToPeers
    nodes[data[0]][data[1]]['ping'] = true
    nodes[data[0]][data[1]]['cfg'] = json
    if (json.hasOwnProperty("delayID")) {
        var to = json.url;
        var pos = to.indexOf(":", 6);
        if (pos > 0) {
            var toDom = to.substring(0, pos + 5);
            comNodes.push({
                'iter': 0, 'fromType': data[0], 'fromDom': data[1], 'url': to,
                'toType': getType(toDom), 'toDom': toDom, 'delayID': json.delayID,
            });
        }
    } 
    drawCanvas();
}

function drawAllComs() {
    var lenc = comNodes.length;
    ctx.save();
    ctx.shadowColor = '#333';
    ctx.shadowBlur = 5;
    ctx.shadowOffsetX = 5;
    ctx.shadowOffsetY = 5;
    var m2 = Math.PI * 2;
    var def = ['rgb(0,0,255)', 'rgb(0,255,255)', 'rgb(0,0,0)'];
    var cols = 0;
    for (var com = 0; com < lenc; com++) {
        var item = comNodes[com];
        if (item.hasOwnProperty('delta')) {
            var node = item.delta;
            var gr = ctx.createRadialGradient(node.x, node.y, node.size / 4, node.x, node.y, node.size);
            cols = def;
            for (var spec in animCol) {
                if (item.show.startsWith(spec)) {
                    cols = animCol[spec];
                    break;
                }
            }
            gr.addColorStop(0, cols[0]);
            gr.addColorStop(0.5, cols[1]);
            gr.addColorStop(1, cols[2]);
            ctx.fillStyle = gr;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, m2, false);
            ctx.closePath();
            ctx.fill();
        }
    }
    ctx.restore();
    var skip = $("#noText").val().split(';');
    if ((skip.length == 1) && (skip[0] == "*")) {
        return;
    }
    var showit = true;
    ctx.fillStyle = "black";
    ctx.font = "10px _sans";
    ctx.textBaseline = "top";

    for (var com = 0; com < lenc; com++) {
        var item = comNodes[com];
        if (item.hasOwnProperty('delta')) {
            showit = true;
            if ((skip.length > 1) || (skip[0].length > 0)) { 
                for (var cn = 0; cn < skip.length; cn++) {
                    if ((skip[cn].trim().length > 0) && (item.show.startsWith(skip[cn].trim()))) {
                        showit = false;
                        break;
                    }
                }
            }
            if (showit) {
                ctx.fillText(item.show, item.delta.x, item.delta.y + (item.delta.toRight ? -item.delta.size * 2 : item.delta.size));
            }
        }
    }
}

function collectRegex(regex) {
    $("#csusp").prop("disabled", false);
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                if (nodes[typ].hasOwnProperty(dom)) {
                    doPOSTCfg(dom + "/visualCfg", { 'active': true, 'pattern': regex });
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
                    doPOSTCfg(dom + "/visualCfg",  { 'active': false, 'pattern': "" });
                }
            }
        }
    }
}

function collectPerType(typ,isLast) {
    for (var dom in nodes[typ]) {
        if (nodes[typ].hasOwnProperty(dom)) {
            if (nodes[typ][dom]['needCollect'] == true) {
                doGETCallback(dom + "/visualGet", collected, [typ, dom]);
            }
        }
    }
    if (isLast) {
        if (collect == true) {
            var tim = +$("#refreshRate").val();
            setTimeout(function () { doCollect(true); }, tim);
        }
    }
}

function doCollect(contin) {
    var lTyp = Object.keys(nodes).length
    if (collect) {
        nodesstate = "cont"
    } else {
        nodesstate = "step"
    }
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            // need to break the link of typ and localise it
            lTyp--;
            (function (useType,isLast) {
                setTimeout(function () { collectPerType(useType,isLast); }, 0);
            })(typ,(lTyp==0) && contin);
        }
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
        collectSuspend();
    }
}

function collectPause() {
    collect = false;
    nodesstate = "loop"
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
    try {
        var xhttp = new XMLHttpRequest();
        //xhttp.onreadystatechange = function () {
        //    if (this.readyState == 4) {
        //        // we ignore reply for now, but maybe can make use of reply for animation....
        //    }
        //};
        xhttp.open("GET", url, false);
        xhttp.send();
    } catch (err) {
        console.log("Error for " + url + " as " + err.message);
        setTimeout(function () { releaseFor(url) }, 100);
    }
}

var mi = Math.floor(maxIter / 3);
function updateCom() {
    var comNodesL = comNodes.length;
    if (comNodesL > 0) {
        var use_x = 0;
        var use_y = 0;
        var toright = true;
        var deltax = 0;
        for (var com = 0; com < comNodesL; com++) {
            var item = comNodes[com];
            if (item.iter == mi) {
                doGETCallback(item.fromDom + "/visualGet", collected, [item.fromType, item.fromDom]);
            }
            if (item.iter >= maxIter) {
                comNodes.splice(com, 1);
                com--;
                comNodesL--;
                releaseFor(item.fromDom + "/visualRelease/" + item.delayID);
                nodes[item.fromType][item.fromDom]['needCollect'] = true;
                continue;
            }
            var from = getXYType(item.fromType, item.fromDom)
            if (from.hasOwnProperty(item.toDom)) {
                var to = getXYType(item.toType, item.toDom);
                deltax = (to.x - from.x) / maxIter * item.iter;
                if (to.x < from.x) {
                    use_y = from.y+ 7;
                    use_x = from.x - 7;
                    toright = false;
                } else {
                    use_y = from.y - 9;
                    use_x = from.x + 9;
                    toright = true
                }

                comNodes[com]['delta'] = { 'x': use_x + deltax, 'y': deltax * from[item.toDom].slope + use_y, 'size': 10, 'toRight': toright };
            } else {
                fact = ((maxIter - item.iter) / maxIter)
                comNodes[com]['delta'] = { 'x': from.x * fact, 'y': from.y * fact, 'size': 10 * fact };
            }
            comNodes[com]['show'] = item.url.substring(item.url.indexOf("/", 8) + 1);
            comNodes[com].iter = comNodes[com].iter + 1;
        }
        if (collect) {
            drawCanvas();
        }
    }
    setTimeout(function () { updateCom() }, +$("#animDelay").val());
}

function doGETCallback(url, callBack, callBackData) {
    try {
        nodes[callBackData[0]][callBackData[1]]['needCollect'] = true
        var xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState == 4) {
                collectCount--;
                callBack(this.responseText, callBackData);
                nodes[callBackData[0]][callBackData[1]]['needCollect'] = true
            }
        };
        xhttp.open("GET", url, true);
        xhttp.send();
        nodes[callBackData[0]][callBackData[1]]['needCollect'] = false
    } catch (err) {
        collectCount--;
        console.log("Error for doGETCallBack" + url + " as " + err.message);  
        nodes[callBackData[0]][callBackData[1]]['ping'] = false
    }
}

function doPOSTCfg(url, data) {
    try {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send((typeof data == 'string') ? data : JSON.stringify(data));
        //var json = { "message": "fail" };
        //json = JSON.parse(xhr.responseText);
        //return [json, xhr.status];
    } catch (err) {
        console.log("Error for doPOSTCfg" + url + " as " + err.message);
    }

}
