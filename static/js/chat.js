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
    window.ws.sock = new WebSocket('ws://127.0.0.1:8888/amqp');
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
        appendMessage(msg["username"],msg["body"]);
    };
    window.ws.send = function (username,msg,routing_key,exchange) {
        console.log('send');
        var m = JSON.stringify({
            "action":"publish",
            "body":msg,
            "username":username,
            "exchange":exchange,
            "routing_key":routing_key
        });
        this.sock.send(m);
    };
};

document.addEventListener("DOMContentLoaded",init_websocket);

function send() {
    var msg = document.getElementById('message').value;
    if (msg.length === 0) {
        return;
    }
    var user = document.getElementById('user').value;
    //appendMessage(user,msg);
    window.ws.send(user,msg,'test','');
    document.getElementById('message').value="";
}
function appendMessage(username,msg) {
    document.getElementById('feed').innerHTML += newMessage(username,msg);
}
function newMessage(username,msg) {
    return '<div class="message"><span class="message-username" style="color:'+USERS[username].color+';">'+username+': </span><span class="message-content">'+msg+'</span></div>';
}

