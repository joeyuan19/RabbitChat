var AMQPWebsocket = function(callbacks) {
    window.pv_amqp_ws = {
        connected:false,
        callbacks:callbacks,
    }
    //var url = window.location.hostname;
    window.pv_amqp_ws.sock = new WebSocket('ws://chat2.joeyuan.com/amqp');
    window.pv_amqp_ws.sock.onopen = function(onopen_db){
        this.connected = true;
        console.log(window.pv_amqp_ws);
        window.pv_amqp_ws.callbacks.onopen();
    };
    var pv_reconnect_timer;
    var delayed_reconnect = function(delay){
        if (typeof delay === "undefined") {
            delay = 5;
        }
        if (delay < 0) {
            console.log("attempting reconnect");
            AMQPWebsocket(window.pv_amqp_ws.callbacks);
            clearTimeout(pv_reconnect_timer);
        } else {
            console.log("AMQPWebsocket: Reconnecting in " + delay + " seconds");
            clearTimeout(pv_reconnect_timer);
            pv_reconnect_timer = setTimeout(function() {
                delayed_reconnect(delay-1);
            },1000);
        }
    }
    window.pv_amqp_ws.sock.onclose = function(evt) {
        console.log("Websocket Error:");
        console.log(evt);
        this.connected = false;
        window.pv_amqp_ws.callbacks.onclose();
        delayed_reconnect(5);
    }
    window.pv_amqp_ws.sock.onerror = function(evt){
        console.log("Websocket Error:");
        console.log(evt);
        this.connected = false;
        window.pv_amqp_ws.callbacks.onerror();
        delayed_reconnect(5);
    }
    window.pv_amqp_ws.sock.onmessage = function(msg){
        msg = JSON.parse(msg.data);
        while (typeof msg !== "object") {
            msg = JSON.parse(msg);
        }
        window.pv_amqp_ws.callbacks.onmessage(msg);
    };
    window.pv_amqp_ws.send = function (username,msg,routing_key,exchange,color) {
        var m = JSON.stringify({
            "action":"publish",
            "body":msg,
            "username":username,
            "color":color,
            "exchange":exchange,
            "routing_key":routing_key,
        });
        console.log(m);
        this.sock.send(m);
        return true;
    };
};
