function tablify(jsonList, order, level, pref, horizontal) {

    var res = "";
    var th = "";
    var useorder = [];
    var suborder = [];
    if (order.length == 0) {
        if (typeof jsonList[0] === "string") {
            // special case
            for (var det = 0; det < jsonList.length; det++) {
                res = res + jsonList[det] + "<br />"
            }
            return res;
        }
        for (var key in jsonList[0]) {
            if (jsonList[0].hasOwnProperty(key)) {
                order.push(pref + key);
                useorder.push(key);
            }
        }
    } else {
        for (var i = 0; i < order.length; i++) {
            var spl = order[i].split(":::");
            if (useorder.indexOf(spl[0]) < 0) {
                useorder.push(spl[0]);
            }
            if (spl.length > 1) {
                var sorder = "";
                for (var j = 1; j < spl.length; j++) {
                    sorder = sorder + spl[j] + ":::";
                }
                suborder.push(sorder.substring(0, sorder.length - 3));
            }
        }
    }

    var col = "style='background-color:#87CEFA'";
    switch (level) {
        case 0:
            col = "style='background-color:#87CEFA'";
            break;
        case 1:
            col = "style='background-color:#6495ED'";
            break;
        case 2:
            col = "style='background-color:#B0E0E6'";
            break;

    }
    if (horizontal) {
        for (var i = 0; i < useorder.length; i++) {
            th = th + "<th " + col + ">" + useorder[i] + "</th>";
        }
    }
    for (var cnt = 0; cnt < jsonList.length; cnt++) {
        if (horizontal) {
            res = res + "<tr><td>" + (cnt + 1) + "</td>";
        }
        for (var det = 0; det < useorder.length; det++) {
            if (jsonList[cnt].hasOwnProperty(useorder[det])) {
                if (!horizontal) {
                    res = res + "<tr><td " + col + ">" + useorder[det] + "</td>";
                }
                if (jsonList[cnt][useorder[det]] instanceof Array) {
                    res = res + "<td>";
                    var wasEmpty = (suborder.length == 0);
                    res = res + tablify(jsonList[cnt][useorder[det]], suborder, level + 1, pref + useorder[det] + ":::", horizontal) + "</td>";
                    if (wasEmpty) {
                        order.push.apply(order, suborder);
                        suborder = [];
                    }
                } else {
                    if ((typeof jsonList[cnt][useorder[det]] != "string") &&
                        (typeof jsonList[cnt][useorder[det]] != "boolean") &&
                        (typeof jsonList[cnt][useorder[det]] != "number")) {
                        res = res + "<td>";
                        var wasEmpty = (suborder.length == 0);
                        res = res + tablify([jsonList[cnt][useorder[det]]], suborder, level + 1, pref + useorder[det] + ":::", horizontal) + "</td>";
                        if (wasEmpty) {
                            order.push.apply(order, suborder);
                            suborder = [];
                        }
                    } else {
                        res = res + "<td>" + jsonList[cnt][useorder[det]] + "</td>";
                    }
                }
            }
            if (!horizontal) {
                res = res + "</tr>";
            }
        }
        if (horizontal) {
            res = res + "</tr>";
        }

    }
    if (horizontal) {
        res = "<table border='1'><th>#</th>" + th + res + "</table>";
    } else {
        res = "<table border='1'>" + res + "</table>";
    }
    return res;
}


function breakup(json) {
    return "<pre>" + JSON.stringify(json, null, 2) + "</pre>";
}

function addCheckBoxes(id, options) {
    options.sort();
    var parentElement = document.getElementById(id);

    for (var count = 0; count < options.length; count++) {
        var newCheckBox = document.createElement('input');
        newCheckBox.type = 'checkbox';
        newCheckBox.id = id + 'opt' + count;
        newCheckBox.classList.add(id + 'opt');
        newCheckBox.value = options[count]
        parentElement.appendChild(newCheckBox);
        parentElement.appendChild(document.createTextNode(options[count] + " "));
    }
}
