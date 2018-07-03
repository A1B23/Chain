    // helper function, but currently port fixex
    function getPort() {
        return 5555;
    }

function doPOSTSynch(url, updateField, data) {
    port = getPort();
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
        xhr.send(JSON.stringify(data));
        var json = { "message": "fail" };
        if (xhr.status == 200) {
            text = xhr.responseText.replace(/\n/g, "");
            json = JSON.parse(xhr.responseText);
            if (updateField != null) {
                var input = document.createElement("textarea");
                input.value = text.replace(/",/g, "\",\r\n").replace(/],/g, "],\r\n");
                input.setAttribute('cols', 40);
                input.setAttribute('rows', 5);
                document.getElementById(updateField).appendChild(input);
            }
        } else {
            json = { "message": xhr.responseText };
        }
        if (updateField != null) {
            document.getElementById(updateField).value = document.getElementById(updateField).value + text;
        }
        return json;
    }
}

function doGETSynch(url) {
    keep = ""
    port = getPort();
    var json = { "message": "fail" };
    if (port < 1024) {
        newContent = "No Port";
    } else {
        var url = fillURL(url);
        //url = getDomain() + ":" + port + "/" + url;
        var xhttp = new XMLHttpRequest();
        xhttp.open("GET", url, false);
        xhttp.send();
        if (xhttp.status == 200) {
            json = JSON.parse(xhttp.responseText)
        } else {
            json = { "message": xhttp.responseText };
        }
    }
    return [json, xhttp.status];
}

function doPOST(url, updateField, getField) {
        port = getPort();
        if (port < 1024) {
            newContent = "Error: No Port";
        } else {
            url = fillURL(url);
            //var url = getDomain() + ":" + port + "/" + url;
            datax = document.getElementById(getField).value.replace(/\\n/g, "");
            var data = JSON.parse(datax);
            //keep = "==> POST / " + url + " with: " + datax;
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function () {
                if (this.readyState == 4) {
                    if (this.status == 200) {
                        text = xhr.responseText.replace(/\n/g, "");
                        var json = JSON.parse(xhr.responseText);
                        var input = document.createElement("textarea");
                        input.value = text.replace(/",/g, "\",\r\n").replace(/],/g, "],\r\n");
                        input.setAttribute('cols', 40);
                        input.setAttribute('rows', 5);
                        document.getElementById(updateField).appendChild(input);
                    } else {
                        text = "Error: " + this.status + " ==> " + xhr.responseText;
                    }
                    document.getElementById(updateField).value = document.getElementById(updateField).value + text
                }
            };
            xhr.open("POST", url, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.send(JSON.stringify(data));
        }
        //keep = addLog(keep, true);
        //addLog("\n   ... waiting for reply ....", false)
    }

    // helper function for debugging the standard API calls to test, configure etc.
    function doGET(url,updateField) {
        keep = ""
        port = getPort();
        if (port < 1024) {
            newContent = "No Port";
        } else {
            var url = fillURL(url);
            //url = getDomain() + ":" + port + "/" + url;
            var xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4) {
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
            //keep = "==> GET / " + url;
        }
        //keep = addLog(keep, true);
        //addLog("\n    ... waiting for reply ....", false)
    }

    function fillURL(inDat) {
        var items = inDat.split("{");
        //var test = inDat.match("/{.+}/g");
        for (var i = 1; i < items.length; i = i + 1) {
            var test = items[i].indexOf("}");
            toReplace = items[i].substr(0, test);
            repl = document.getElementById("p" + toReplace).value;
            inDat = inDat.replace("{" + toReplace + "}", repl);
        }
        return inDat;
    }