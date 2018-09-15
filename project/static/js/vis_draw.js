diffCol = ['black', 'orange', 'red', ',magenta', 'cyan', 'blue', 'purple'];

function hintinit() {
    allhint = { 'b': [] , 'm': [], 'w': []};
}


function drawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    collectSizeRotate();
    calcCoords();
    if (document.getElementById('useGrid').checked) { 
        drawGrid();
    }
    drawLines();
    ctx.save();
    ctx.shadowColor = '#555';
    ctx.shadowBlur = 6;
    ctx.shadowOffsetX = 7;
    ctx.shadowOffsetY = 7;
    drawAllNodes();
    ctx.restore();
    ctx.save();
    annotateAllNodes();
    ctx.restore();
    drawAllComs();
}


var mp2 = Math.PI * 2;
var m7 = Math.PI / 7;
var p180 = Math.PI / 180;

function drawGrid() {
    ctx.setLineDash([3, 6])
    var sradx = Math.trunc((getWidth() * .45) / rings.length);
    var srady = Math.trunc((getHeight() * .45) / rings.length);
    var center_x = getWidth()>> 1;
    var center_y = getHeight() >> 1;
    ctx.strokeStyle = "lightgrey";
    ctx.fillStyle = "lightgrey";
    ctx.lineWidth = 1;
    ctx.strokeWidth = 1;

    for (var ring = 1; ring <= rings.length; ring++) {
        ctx.beginPath();
        ctx.ellipse(center_x, center_y, sradx * ring, srady * ring, 0, mp2, false);
        ctx.stroke();
    }
    ctx.setLineDash([])
}

function resizeCanvas() {
    ctx.canvas.width = getWidth();
    ctx.canvas.height = getHeight();
    drawCanvas();
}


function drawNode(typ, dom, node, cols) {
    var n = nodes[typ];
    if (n.hasOwnProperty(dom)) {
        var item = n[dom]
        if (item['ping'] === true) {
            var gr = ctx.createRadialGradient(node.x - (node.size >> 1), node.y - (node.size >> 1), node.size / 5, node.x, node.y, node.size);
            gr.addColorStop(0, cols[0]);
            gr.addColorStop(0.75, cols[1]);
            gr.addColorStop(1, cols[2]);
            ctx.fillStyle = gr;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0,mp2 , false);
            ctx.closePath();
            ctx.fill();
        } else {
            var gr = ctx.createRadialGradient(node.x, node.y, node.size >> 2, node.x, node.y, node.size);
            gr.addColorStop(0, cols[0]);
            gr.addColorStop(0.5, "red");
            gr.addColorStop(1, "orange");
            ctx.fillStyle = gr;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, mp2, false);
            ctx.closePath();
            ctx.fill();
        }
        return true;
    }
    return false;
}


function annotateNode(typ, dom, node, cols) {
    var n = nodes[typ];
    if (n.hasOwnProperty(dom)) {
        var item = n[dom]
        var ipa = typ
        var pos = dom.lastIndexOf(":")
        if (pos > 0) {
            ipa = dom.substring(0, pos);
            pos = ipa.lastIndexOf(".");
            if (pos > 0) {
                ipa = typ + "/" + ipa.substring(pos + 1);
            }
        }
        ctx.fillStyle = "black";
        ctx.font = "bold 10px _sans";
        ctx.fillText(ipa, node.x - node.size / 2, node.y + node.size*1.2);
        var hint = "";
        if (typ.startsWith("B") || typ.startsWith("*B")) {
            var cfg = item['cfg'];
            hint += "" + (cfg['chainHeight'] - 1) + " / #Tx:" + cfg['pendTX'];
            var c = cfg['blockHash'];
            var i = 0;
            while ((i < c.length) && (c[i] == "0")) {
                i++;
            }
            hint += " / d:" + i + " (..." + c.substring(c.length - 7) + ")"
            setColorNode('b', hint);
        } else if (typ.startsWith("M") || typ.startsWith("*M")) {
            var cfg = item['cfg']
            hint += "" + cfg['nonceCnt'];
            setColorNode('m', hint);
        } else if (typ.startsWith("W") || typ.startsWith("*W")) {
            var cfg = item['cfg']
            hint += "" + cfg['lastBal'];
            setColorNode('w', hint);
        }
        if (hint.length > 0) {
            ctx.fillText(hint, node.x - node.size * 2 / 3 - hint.length, node.y - 1.5 * node.size);
        }
        return true;
    }
    return false;
}

function setColorNode(type, hint) {

    if (type == 'b') {
        ctx.font = "12px _sans";
        var idx = allhint[type].indexOf(hint);
        if (idx < 0) {
            allhint[type].push(hint);
            idx = allhint[type].length - 1;
        }
        ctx.fillStyle = diffCol[Math.min(diffCol.length - 1, idx)];
    } else if (type == 'm') {
        ctx.font = "italic 11px _sans";
    }
}

function drawLines() {

    var drawFrom = 0
    var drawTo = 0;
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                if (nodes[typ].hasOwnProperty(dom)) {
                    for (var peer in nodes[typ][dom]['shareToPeers']) {
                        ctx.lineWidth = .5;
                        drawFrom = nodes[typ][dom]['draw'];
                        drawTo = getXY(peer);
                        ctx.strokeStyle = '#00FF7F';
                        if (nodes[typ][dom]['ping'] == false) {
                            ctx.strokeStyle = 'orange';
                        }
                        ctx.beginPath();
                        ctx.moveTo(drawFrom.x - 1, drawFrom.y + 1);
                        ctx.lineTo(drawTo.x + 1, drawTo.y - 1);
                        ctx.stroke();
                        ctx.closePath();
                        ctx.strokeStyle = '#32CD32';
                        arrow(drawFrom, drawTo, 3);
                    }
                    ctx.lineWidth = .2;
                    for (var peer in nodes[typ][dom]['activePeers']) {
                        drawFrom = nodes[typ][dom]['draw'];
                        drawTo = getXY(peer);
                        ctx.strokeStyle = '#2E8B57';
                        if (nodes[typ][dom]['ping'] == false) {
                            ctx.strokeStyle = 'orange';
                        }
                        ctx.beginPath();
                        ctx.moveTo(drawFrom.x, drawFrom.y);
                        ctx.lineTo(drawTo.x, drawTo.y);
                        ctx.stroke();
                        ctx.closePath();
                        ctx.strokeStyle = '#006400';
                        arrow(drawFrom, drawTo,5);
                    }
                }
            }
        }
    }
}


function drawAllNodes() {
    var dx = 0;
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                dx = getXYType(typ, dom);
                if (Object.keys(dx).length > 2) {
                    drawNode(typ, dom, dx, col[typ]);
                }
            }
        }
    }
}

function annotateAllNodes() {
    var dx = 0;
    ctx.textBaseline = "top";
    hintinit();
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                dx = getXYType(typ, dom);
                if (Object.keys(dx).length > 2) {
                    annotateNode(typ, dom, dx, col[typ]);
                }
            }
        }
    }
}


function drawArrow(fromx, fromy, tox, toy, size) {
    var angle = Math.atan2(toy - fromy, tox - fromx);
    var start = tox - size * Math.cos(angle - m7);
    var end = toy - size * Math.sin(angle - m7);
    //ctx.strokeStyle = "red";
    ctx.beginPath();
    ctx.moveTo(tox, toy);
    ctx.lineTo(start, end);

    ctx.lineTo(tox - size * Math.cos(angle + m7), toy - size * Math.sin(angle + m7));
    ctx.lineTo(tox, toy);
    ctx.lineTo(start,end);

    ctx.lineWidth = 5;
    ctx.stroke();
    ctx.closePath();
    ctx.fill();
}

function arrow(from, to,size) {
    var mx = (from.x + to.x) >> 1;
    var my = (from.y + to.y) >> 1;
    drawArrow(from.x, from.y, ((from.x + mx) / 2 + mx) >> 1, ((from.y + my) / 2 + my) >> 1, size);
}

function calcSlope(typ,dom,type, drawFrom) {
    for (var peer in nodes[typ][dom][type]) {
        if (nodes[typ][dom][type].hasOwnProperty(peer)) {
            var drawTo = getXY(peer);
            if (Object.keys(drawTo).length > 0) {
                nodes[typ][dom]['draw'][peer] = { 'slope': (drawTo.y - drawFrom.y) / (drawTo.x - drawFrom.x) };
            }
        }
    }
}


function calcCoords() {
    var sradx = Math.trunc((getWidth() * .45) / rings.length);
    var srdx23 = (sradx * 2 / 3);
    var srady = Math.trunc((getHeight() * .45) / rings.length);
    var srdy23 = (srady * 2 / 3);

    var center_x = getWidth() >> 1;
    var center_y = getHeight() >> 1;

    for (var ring = 0; ring < rings.length; ring++) {
        r = rings[ring];
        var radiusx = sradx * (ring + 1);
        var radiusy = srady * (ring + 1);
        var r360 = (setSizes[ring] / 100);
        var size = srdx23 * r360;
        size = Math.min(size, srdy23 * r360);
        r360 = (360 / r.length);
        for (var rr = 0; rr < r.length; rr++) {
            var angle = (r360 * rr + rot[ring]) * p180;
            var x = center_x + radiusx * Math.cos(angle);
            var y = center_y + radiusy * Math.sin(angle);
            if (!setXY("B", r[rr], x, y, size)) {
                if (!setXY("W", r[rr], x, y, size)) {
                    if (!setXY("M", r[rr], x, y, size)) {
                        if (!setXY("F", r[rr], x, y, size)) {
                            //???
                        }
                    }
                }
            }
        }
    }

    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                if (nodes[typ].hasOwnProperty(dom)) {
                    var drawFrom = getXY(dom);
                    calcSlope(typ, dom, 'activePeers', drawFrom);
                    calcSlope(typ, dom, 'shareToPeers', drawFrom);
                }
            }
        }
    }
}

