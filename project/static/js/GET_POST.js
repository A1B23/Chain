    // helper function, but currently port fixex
    function getPort() {
        return 5555;
    }

function doDirect(url, ext) {
    // TODO insert a try catch
    var id = "#result" + ext;
    var repl = doGETSynch(url);
    var json = repl[0];
    var code = repl[1];
    if (code == 200) {
        var opts = []
        var addOptions = true;
        $(".options" + ext + "opt").each(function () {
            addOptions = false;
            if ($(this).is(':checked')) {
                opts.push($(this).val());
            }
        });
        if (document.getElementById("useTable").checked) {
            var horizontal = document.getElementById("useHorizontal").checked
            if (json instanceof Array) {
                $(id).html(tablify(json, opts, 0, "", horizontal));
            } else {
                $(id).html(tablify([json], opts, 0, "", horizontal));
            }
            if (addOptions) {//first time
                addCheckBoxes("options" + ext, opts)
            }
        } else {
            $(id).html(breakup(json));
        }
    } else {
        $(id).text("Command rejected with reason: " + JSON.stringify(json));
    }
}


function doPOSTSynch(url, updateField, data) {
    var port = getPort();
    if (port < 1024) {
        newContent = "Error: No Port";
    } else {
        url = fillURL(url);
        //var url = getDomain() + ":" + port + "/" + url;
        //datax = document.getElementById(getField).value.replace(/\\n/g, "");
        //var data = JSON.parse(datax);
        //keep = "==> POST / " + url + " with: " + datax;


        var xhr = new XMLHttpRequest();
        xhr.open("POST", url, false);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send((typeof data == 'string')?data:JSON.stringify(data));
        var jsond = { "message": "fail" };
        if ((xhr.status == 200) || (xhr.status == 201)) {
            var text = xhr.responseText.replace(/\n/g, "");
            jsond = JSON.parse(xhr.responseText);
            if (updateField != null) {
                var input = document.createElement("textarea");
                input.value = text.replace(/",/g, "\",\r\n").replace(/],/g, "],\r\n");
                input.setAttribute('cols', 40);
                input.setAttribute('rows', 5);
                document.getElementById(updateField).appendChild(input);
            }
        } else {
            jsond = JSON.parse(xhr.responseText);
        }
        if (updateField != null) {
            document.getElementById(updateField).value = document.getElementById(updateField).value + text;
        }
        return [jsond,xhr.status];
    }
}

function doGETSynch(url) {
    var keep = ""
    var port = getPort();
    var json = { "message": "fail" };
    if (port < 1024) {
        var newContent = "No Port";
    } else {
        var url = fillURL(url);
        //url = getDomain() + ":" + port + "/" + url;
        var xhttp = new XMLHttpRequest();
        xhttp.open("GET", url, false);
        xhttp.send();
        var jsond = "";
        if (xhttp.status != 500) {
            jsond = JSON.parse(xhttp.responseText)
        } else {
            jsond = JSON.parse("No peer available...");
        }
    }
    return [jsond, xhttp.status];
}

function doPOST(url, updateField, getField) {
        var port = getPort();
        if (port < 1024) {
            var newContent = "Error: No Port";
        } else {
            var url = fillURL(url);
            //var url = getDomain() + ":" + port + "/" + url;
            var datax = document.getElementById(getField).value.replace(/\\n/g, "");
            var data = JSON.parse(datax);
            //keep = "==> POST / " + url + " with: " + datax;
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function () {
                if (this.readyState == 4) {
                    var text =""
                    if (this.status == 200) {
                        text = xhr.responseText.replace(/\n/g, "");
                        if (updateField.length > 0) {
                            var json = JSON.parse(xhr.responseText);
                            var input = document.createElement("textarea");
                            input.value = text.replace(/",/g, "\",\r\n").replace(/],/g, "],\r\n");
                            input.setAttribute('cols', 40);
                            input.setAttribute('rows', 5);
                            document.getElementById(updateField).appendChild(input);
                            return;
                        }
                    } else {
                        text = "Error: " + this.status + " ==> " + xhr.responseText;
                    }
                    if (updateField.length > 0) {
                        var input = document.createElement("textarea");
                        input.value = text.replace(/",/g, "\",\r\n").replace(/],/g, "],\r\n");
                        input.setAttribute('cols', 40);
                        input.setAttribute('rows', 5);
                        document.getElementById(updateField).appendChild(input);
                    }
                }
            };
            xhr.open("POST", url, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.send(JSON.stringify(data));
        }
    }

    // helper function for debugging the standard API calls to test, configure etc.
    function doGETCallback(url, callBack,callBackData) {
        var keep = ""
        var port = getPort();
        if (port < 1024) {
            var newContent = "No Port";
        } else {
            var url = fillURL(url);
            var xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4) {
                    callBack(this.responseText, callBackData);
                }
            };
            xhttp.open("GET", url, true);
            xhttp.send();
        }
    }
    function doGET(url,updateField) {
        var keep = ""
        var port = getPort();
        if (port < 1024) {
            var newContent = "No Port";
        } else {
            var url = fillURL(url);
            //url = getDomain() + ":" + port + "/" + url;
            var xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4) {
                    var text = ""
                    if (this.status == 200) {
                        text = this.responseText;
                    } else {
                        text = "Error: " + this.status + " ==> " + this.responseText;
                    }
                    document.getElementById(updateField).value = document.getElementById(updateField).value + text
                }
            };
            xhttp.open("GET", url, true);
            xhttp.send();
        }
    }

    function fillURL(inDat) {
        var items = inDat.split("{");
        for (var i = 1; i < items.length; i = i + 1) {
            var test = items[i].indexOf("}");
            var toReplace = items[i].substr(0, test);
            var repl = document.getElementById("p" + toReplace).value;
            inDat = inDat.replace("{" + toReplace + "}", repl);
        }
        return inDat;
}

function setClrPeer(out, data, use, add) {
    setClearPeer(out, data, use, document.getElementById(add).checked);
}

function setPeer(out, data, use) {
    setClearPeer(out, data, use, true);
}

function setClearPeer(out, data, use, add) {
    document.getElementById(out).innerHTML = "";
    document.getElementById(use).value = '{ "peerUrl": "' + document.getElementById(data).value + '" }';
    if (add) {
        doPOST('peers/connect', out, use);
    } else {
        doPOST('peers/disconnect', out, use);
    }
}