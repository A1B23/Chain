function drawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    collectSizes();
    calcCoords();
    drawGrid();
    drawLines();
    ctx.save();
    setShadow(true);
    drawAllNodes();
    ctx.restore();
    drawAllComs();
}

function drawGrid() {
    ctx.setLineDash([5, 5])
    var sradx = Math.trunc((getWidth() * .45) / (rings.length * 1));
    var srady = Math.trunc((getHeight() * .45) / (rings.length * 1));
    var center_x = getWidth() / 2;
    var center_y = getHeight() / 2;
    ctx.strokeStyle = "lightgrey";
    ctx.fillStyle = "lightgrey";
    ctx.lineWidth = 1;
    ctx.strokeWidth = 1;

    for (var ring = 1; ring <= rings.length; ring++) {
        ctx.beginPath();
        ctx.ellipse(center_x, center_y, sradx * ring, srady * ring, 0, 2 * Math.PI, false);
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
            var gr = ctx.createRadialGradient(node.x, node.y, node.size / 4, node.x, node.y, node.size);
            gr.addColorStop(0, cols[0]);
            gr.addColorStop(0.5, cols[1]);
            gr.addColorStop(1, cols[2]);
            ctx.fillStyle = gr;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2, false);
            ctx.closePath();
            ctx.fill();
        } else {
            var gr = ctx.createRadialGradient(node.x, node.y, node.size / 4, node.x, node.y, node.size);
            gr.addColorStop(0, cols[0]);
            gr.addColorStop(0.5, "red");
            gr.addColorStop(1, "orange");
            ctx.fillStyle = gr;
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2, false);
            ctx.closePath();
            ctx.fill();
        }
        ctx.fillStyle = "black";
        ctx.font = "10px _sans";
        ctx.textBaseline = "top";
        var ipa = typ
        var pos = dom.lastIndexOf(":")
        if (pos > 0) {
            ipa = dom.substring(0, pos);
            pos = ipa.lastIndexOf(".");
            if (pos > 0) {
                ipa = typ + "/" + ipa.substring(pos + 1);
            }
        }
        ctx.fillText(ipa, node.x - node.size / 2, node.y);
        return true;
    }
    return false;
}

function drawLines() {
    //nodes[typ][dom] = { "ping": true, "ring": ring, "cfg": jstext };
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                if (nodes[typ].hasOwnProperty(dom)) {
                    var drawFrom = getXY(dom);
                    for (var peer in nodes[typ][dom]['peers']) {
                        if (nodes[typ][dom]['peers'].hasOwnProperty(peer)) {
                            var drawTo = getXY(peer);
                            if (Object.keys(drawTo).length > 0) {
                                ctx.strokeStyle = 'green';
                                if (nodes[typ][dom]['ping'] == false) {
                                    ctx.strokeStyle = 'orange';
                                }
                                ctx.lineWidth = 2;
                                ctx.beginPath();
                                ctx.moveTo(drawFrom.x, drawFrom.y);
                                ctx.lineTo(drawTo.x, drawTo.y);
                                ctx.stroke();
                                ctx.closePath();
                                arrow(drawFrom, drawTo);
                            }
                            else {
                                ctx.strokeStyle = 'red';
                                ctx.lineWidth = 2;
                                ctx.beginPath();
                                ctx.moveTo(drawFrom.x, drawFrom.y);
                                ctx.lineTo(0, 0);
                                ctx.stroke();
                                ctx.closePath();
                            }

                        }
                    }
                }
            }
        }
    }
}


function drawAllNodes() {
    for (var typ in nodes) {
        if (nodes.hasOwnProperty(typ)) {
            for (var dom in nodes[typ]) {
                var dx = getXYType(typ, dom);
                if (Object.keys(dx).length > 2) {
                    drawNode(typ, dom, dx, col[typ]);
                }
            }
        }
    }
}


function drawArrow(fromx, fromy, tox, toy, size) {
    //variables to be used when creating the arrow
    var headlen = size;

    var angle = Math.atan2(toy - fromy, tox - fromx);

    //starting a new path from the head of the arrow to one of the sides of the point
    ctx.beginPath();
    ctx.moveTo(tox, toy);
    ctx.lineTo(tox - headlen * Math.cos(angle - Math.PI / 7), toy - headlen * Math.sin(angle - Math.PI / 7));

    //path from the side point of the arrow, to the other side point
    ctx.lineTo(tox - headlen * Math.cos(angle + Math.PI / 7), toy - headlen * Math.sin(angle + Math.PI / 7));

    //path from the side point back to the tip of the arrow, and then again to the opposite side point
    ctx.lineTo(tox, toy);
    ctx.lineTo(tox - headlen * Math.cos(angle - Math.PI / 7), toy - headlen * Math.sin(angle - Math.PI / 7));

    //draws the paths created above
    ctx.lineWidth = 5;
    ctx.stroke();
    ctx.fill();
}

function arrow(from, to) {
    var mx = (from.x + to.x) / 2;
    var my = (from.y + to.y) / 2;
    var mx2 = (from.x + mx) / 2;
    var my2 = (from.y + my) / 2;
    mx = (mx2 + mx) / 2;
    my = (my2 + my) / 2;
    drawArrow(from.x, from.y, mx, my, 1);
}

function calcCoords() {
    var sradx = Math.trunc((getWidth() * .45) / (rings.length * 1));
    var srady = Math.trunc((getHeight() * .45) / (rings.length * 1));

    var center_x = getWidth() / 2;
    var center_y = getHeight() / 2;

    for (var ring = 0; ring < rings.length; ring++) {
        r = rings[ring];
        var radiusx = sradx * (ring + 1);
        var radiusy = srady * (ring + 1);
        var size = (sradx * 2 / 3) * (setSizes[ring] / 100);
        size = Math.min(size, (srady * 2 / 3) * (setSizes[ring] / 100));
        for (var rr = 0; rr < r.length; rr++) {
            var angle = ((360 / r.length) * rr + rot[ring]) * Math.PI / 180;
            var x = center_x + radiusx * Math.cos(angle);
            var y = center_y + radiusy * Math.sin(angle);
            if (!setXY("B", r[rr], x, y, size)) {
                if (!setXY("W", r[rr], x, y, size)) {
                    if (!setXY("M", r[rr], x, y, size)) {
                        //???
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
                    for (var peer in nodes[typ][dom]['peers']) {
                        if (nodes[typ][dom]['peers'].hasOwnProperty(peer)) {
                            var drawTo = getXY(peer);
                            if (Object.keys(drawTo).length > 0) {
                                var slope = (drawTo.y - drawFrom.y) / (drawTo.x - drawFrom.x);
                                nodes[typ][dom]['draw'][peer] = { 'slope': slope };
                            }
                        }
                    }
                }
            }
        }
    }
}