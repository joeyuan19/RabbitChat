var get_username = function() {
    return document.getElementById('username').value;
}

var get_color = function() {
    return document.getElementById('color').value;
}

window.ws = {
    connected:false,
}
var init_websocket = function() {
    var url = window.location.href;
    if (url[url.length-1] == "/") {
        url = url.slice(0,url.length-1);
    }
    if (url.indexOf("http://") === 0) {
        url = url.slice("http://".length);
    }
    window.ws.sock = new WebSocket('ws://'+url+'/amqp');
    window.ws.sock.onopen = function(){
        this.connected = true;
        document.getElementById('connection-status').style['background'] = 'green';
        document.getElementById('connection-status').innerHTML = 'Connected';
    };
    var countdown = function(){
        var n = parseInt(document.getElementById('count').innerHTML);
        if (n < 0) {
            init_websocket();
        } else {
            document.getElementById('count').innerHTML=n-1;
            setTimeout(countdown,1000);
        }
    }
    var error_reconnect = function(){
        console.log('Error');
        this.connected = false;
        document.getElementById('connection-status').style['background'] = 'red';
        document.getElementById('connection-status').innerHTML = 'Disconnected.  Reconnecting in <span id="count">5</span>';
        countdown();
    }
    window.ws.sock.onclose = error_reconnect; 
    window.ws.sock.onerror = error_reconnect; 
    window.ws.sock.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        while (typeof msg !== "object") {
            msg = JSON.parse(msg);
        }
        console.log("message received");
        appendMessage(msg["username"],msg["body"],msg["color"],msg["timestamp"]);
    };
    window.ws.send = function (username,msg,routing_key,exchange,color) {
        document.getElementById('error').innerHTML='';
        var m = JSON.stringify({
            "action":"publish",
            "body":msg,
            "timestamp":timestamp(),
            "username":username,
            "exchange":exchange,
            "routing_key":routing_key,
            "color":color
        });
        this.sock.send(m);
    };
};

function timestamp() {
    var time = new Date();
    var s = time.getSeconds()+"";
    if (s.length < 2) {
        s = "0"+s;
    }
    var m = time.getSeconds()+"";
    if (m.length < 2) {
        m = "0"+m;
    }
    return time.getHours()+":"+m+":"+s+" "+time.getMonth()+"/"+time.getDay()+"/"+time.getFullYear();
}

document.addEventListener("DOMContentLoaded",init_websocket);

function send() {
    var msg = document.getElementById('message').value;
    var user = get_username(), color = get_color();
    if (msg.length === 0) {
        document.getElementById('error').innerHTML='There is no text in the message box';
        return;
    }
    if (user.length === 0) {
        document.getElementById('error').innerHTML='Please enter a username';
        return;
    }
    window.ws.send(user,msg,'test','',color);
    document.getElementById('message').value="";
}
function appendMessage(username,msg,color,time) {
    document.getElementById('feed').innerHTML += newMessage(username,msg,color,time);
    document.getElementById('feed').scrollTop = document.getElementById('feed').scrollHeight; 

}
function newMessage(username,msg,color,time) {
    return '<div class="message"><span class="message-username" style="color:'+color+';">'+username+'<span class="timestamp"> ('+time+')</span>: </span><span class="message-content">'+msg+'</span></div>';
}

var checkSend = function(evt){
    evt = window.event || evt;
    var key = evt.which || evt.keyCode;
    if (key == 13) {
        send();
        if (window.event) {
            window.event.returnValue = false;
        } else {
            evt.preventDefault();
        }
    }
    return true;
}
var toggleTime = function() {
    var elms = document.getElementsByClassName('timestamp');
    console.log(elms);
    if (elms.length === 0) {
        return;
    }
    if (elms[0].style.display === "none") {
        var state = "inline";
        document.getElementById('time').innerHTML='Hide Timestamps';
    } else {
        var state = "none";
        document.getElementById('time').innerHTML='Show Timestamps';
    }
    for (var i = 0; i < elms.length; i++) {
        elms[i].style.display = state;
    }
}

