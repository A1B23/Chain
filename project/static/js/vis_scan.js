function newScan() {
    collectPause();
    collectSuspend();
    init();
    //ctx.clearRect(0, 0, canvas.width, canvas.height);
    //collectSizes();
    //drawGrid();
    setTimeout(function () { reScan(true); }, 10);
}

function scTime(xipx, xtyp, xring, xinit) {
    (function (xxipx, xxtyp, xxring, xxinit) {
        setTimeout(function () {
            scanFor(xxipx, xxtyp, xxring, xxinit);
        }, 0);
    })(xipx, xtyp, xring, xinit);
    
}

function reScan(init) {
    //console.log("============================================="+Date.now());
    var ring = 0;
    $("td[id*='opt']").each(function () {
        var min = parseInt($(this).find("#IPMin")[0].value);
        var max = parseInt($(this).find("#IPMax")[0].value);
        var typ = $(this).find("#type")[0];
        if ((min * max > 0) && (min > 0) && (min < 128) && (max < 128)) {
            for (var ipx = min; ipx <= max; ipx++) {
                scTime(ipx, typ.value, ring, init);
            }
        }
        ring++;
        //console.log("__________________________________" + ring);
    });
    var sc = $("#scan");
    if (sc.is(":checked")) {
        //console.log("_____________________________________________________________________________"+Date.now());
        setTimeout(function () { reScan(false) }, 3000);
    }
}

function scanFor(ipIn, typIn, ringIn, init) {
    (function (ipIn, typIn, ringIn, init) {
        var ip = ipIn;
        var typ = typIn.substring(0, 1);
        var ring = ringIn;
        var port = 5555
        var dom = "http://127.0.0." + ip + ":" + port;
        var url = dom + "/cfg";
        var xhttp = new XMLHttpRequest();
        if (init == true) {
            nodesstate = "init";
        }
        if (nodesstate == "cont") {
            if (hasNode(typ, dom)) {
                // no need to check again, it is continuously probed by the visual nodes?
                if (ringIn == nodes[typ][dom]['ring']) {
                    if (nodes[typ][dom].hasOwnProperty('ping')) {
                        if (nodes[typ][dom]['ping'] == true) {
                            return
                        }
                    }
                } 
                delete nodes[typ][dom];
                delete rings[ringIn][dom]
                var cdom = clearDom(dom);
                if ($("#" + cdom).length != 0) {
                    $("#" + cdom).remove();
                }
            }
        }
        xhttp.onreadystatechange = function () {
            if (this.readyState == 4) {
                addLog("\n(" + typ + ") Reply:" + url, false);
                if (ring >= 4) {
                    if (nodesstate == 'init') {
                        nodesstate = "loop";
                    }
                }
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
                        //if (avail.hasOwnProperty(dom)) {
                        //    nodes[typ][dom]["ping"] = true;
                        //} else {
                        //console.log("has " + Object.keys(nodes['B']).length + "/" + Object.keys(nodes['W']).length
                        //    + "/" + Object.keys(nodes['M']).length + "/" + Object.keys(nodes['F']).length);
                        nodes[typ][dom] = {
                            "ping": true, "ring": ring, "cfg": jstext,
                            "activePeers": jstext['activePeers'],
                            "shareToPeers": jstext['shareToPeers'],
                            "needCollect": true
                        };
                        //console.log(nodes[typ][dom]);
                        //}

                        if (!text.startsWith("[]")) {
                            addLog("\n" + text, false);
                        } else {
                            addLog(" ===> []", false);
                        }
                        if (found == false) {
                            var cdom = clearDom(dom);
                            //if ($("#" + cdom).length == 0) {
                            $('<iframe src="' + dom + '" frameborder="1" class="iframes" scrolling="yes" id="' + cdom + '" title="' + dom + '" width="100%"></iframe>')
                                .appendTo('#control').hide();
                            setFramesHeight();
                            //}
                        }
                        //if (ring >= 4) {
                            drawCanvas();
                        //}
                    } else {
                        addLog("Wrong node detected in range: " + jstext['type'] + "for ring " + ring + " expected " + typ);
                    }
                } else {
                    text = " ==> Error: " + this.status + " with '" + this.responseText + "'";
                    addLog(text, false);
                    if (hasNode(typ, dom)) {
                        nodes[typ][dom]['ping'] = false;
                    }
                    drawCanvas();
                }
                
            }
        };
        xhttp.open("GET", url, true);
        xhttp.send();
    })(ipIn, typIn, ringIn, init);
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

function hasNode(typ, dom) {
    if (nodes.hasOwnProperty(typ)) {
        return nodes[typ].hasOwnProperty(dom);
    }
    return false;
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