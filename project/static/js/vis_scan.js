function newScan() {
    collectPause();
    init();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    collectSizes();
    drawGrid();
    reScan();
}

function reScan() {
    initScan = false;
    if (totalScan <= 0) {
        var scans = [];
        var ring = 0;
        $("td[id*='opt']").each(function () {
            var min = parseInt($(this).find("#IPMin")[0].value);
            var max = parseInt($(this).find("#IPMax")[0].value);
            var typ = $(this).find("#type")[0];
            // TODO alert ignore double
            if ((min * max > 0) && (min > 0) && (min < 128) && (max < 128)) {
                for (var ipx = min; ipx <= max; ipx++) {
                    //TODO get the scan directly here and only update the relevant ring!!!
                    scans.push([ipx, typ.value, ring]);
                }
            }
            ring++;
        });
        totalScan = scans.length
        for (var i = 0; i < scans.length; i++) {
            scanFor(scans[i][0], scans[i][1], scans[i][2]);
        }
        scans = [];
    }
    var sc = $("#scan");
    if (sc.is(":checked")) {
        setTimeout(function () { reScan() }, 5000);
    }
}

function scanFor(ipIn, typIn, ringIn) {
    var ip = ipIn;
    var typ = typIn.substring(0, 1);
    var ring = ringIn;
    var port = 5555
    var dom = "http://127.0.0." + ip + ":" + port
    var url = dom + "/cfg";
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            addLog("\n(" + typ + ") Reply:" + url, false);
            var avail = nodes[typ]
            if (this.status == 200) {
                var text = this.responseText;
                var jstext = JSON.parse(text);
                var corTyp = (jstext['type'].startsWith(typ));
                if (!corTyp) {
                    corTyp = (jstext['type'].startsWith("*" + typ));
                    typ = "*" + typ;
                }
                if (corTyp) {
                    var found = false
                    for (var i = 0; i < rings[ring].length; i++) {
                        if (rings[ring][i] == dom) {
                            found = true;
                            break;
                        }
                    }
                    if (found == false) {
                        rings[ring].push(dom);
                    }
                    if (avail.hasOwnProperty(dom)) {
                        nodes[typ][dom]['ping'] = true;
                    } else {
                        nodes[typ][dom] = { "ping": true, "ring": ring, "cfg": jstext, "peers": jstext['peers'] };
                    }

                    if (!text.startsWith("[]")) {
                        addLog("\n" + text, false);
                    } else {
                        addLog(" ===> []", false);
                    }
                    if (found == false) {
                        $('<iframe src="' + dom + '" frameborder="1" class="iframes" scrolling="yes" id="' + clearDom(dom) + '" title="' + dom + '" width="100%"></iframe>')
                            .appendTo('#control').hide();
                        setFramesHeight();
                    }
                } else {
                    addLog("Wrong node detected in range: " + jstext['type'] + "for ring " + ring + " expected " + typ);
                }
            } else {
                text = " ==> Error: " + this.status + " with '" + this.responseText + "'";
                addLog(text, false);
                if (avail.hasOwnProperty(dom)) {
                    nodes[typ][dom]['ping'] = false;
                } else {

                }
            }
            totalScan--;
            drawCanvas();
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function setXY(typ, dom, x, y, size) {
    if (nodes.hasOwnProperty(typ) && nodes[typ].hasOwnProperty(dom)) {
        nodes[typ][dom]['draw'] = { 'x': x, 'y': y, 'size': size };
    } else if (nodes.hasOwnProperty("*"+typ) && nodes["*"+typ].hasOwnProperty(dom)) {
        nodes["*"+typ][dom]['draw'] = { 'x': x, 'y': y, 'size': size };
    }
}

function getXYType(typ, dom) {
    if (nodes.hasOwnProperty(typ)) {
        if (nodes[typ].hasOwnProperty(dom)) {
            return nodes[typ][dom]['draw'];
        }
    }
    return {}
}

function getXY(dom) {
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            if (nodes[typ].hasOwnProperty(dom)) {
                return nodes[typ][dom]['draw'];
            }
        }
    }
    return {}
}

function getType(dom) {
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            if (nodes[typ].hasOwnProperty(dom)) {
                return typ;
            }
        }
    }
    console.log("not found " + dom);
    return "";
}