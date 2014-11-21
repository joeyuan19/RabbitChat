var get_color = function() {
    var hex = "";
    for (var i = 0; i < 3; i++) {
        hex += (48+Math.floor((256-48)*Math.random())).toString(16);
    }
    return "#"+hex;
}
var get_username = function() {
    var names = [
        "Lil Jon",
        "Fat Joe",
        "Tupac Shakur",
        "Biggie Smalls",
        "Lil Wayne",
        "Nelly",
        "50cent",
        "Ghostface Killah",
        "Ol' Dirty Bastard",
        "Fabulous",
        "Ludacris",
        "Yak Ballz",
        "Common",
        "Young Jeezy",
        "Kanye West",
        "Jay-Z",
        "Snoop Dogg",
        "Easy-E",
        "Ice Cube",
        "The Rizzah",
        "Puff Daddy",
        "Rick Ross",
        "Titty Boi",
        "2Chainz",
        "Soulja Boy Tell'Em",
        "The Game",
        "Inspectah Deck",
        "Kendrick Lamar",
        "Mos Def",
        "MF DOOM",
        "Smif-N-Wessun"
    ];
    return names[Math.floor(1+names.length*Math.random())]
}
window.pv_color = get_color()
window.pv_username = get_username()
var generate_html = function() {
    return '<div id="pv-container">'+
'    <link rel="stylesheet" href="/static/css/peerview.css"/>'+
'    <link href="http://maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css" rel="stylesheet">'+
'<div id="pv-pin" class="pv-pin">' +
'    <i class="fa fa-plus fa-lg pv-icon"></i>'+
'</div>'+
'<div id="pv-box" class="pv-thread-container">'+
'    <div id="pv-connection-light"></div>'+
'    <div id="pv-chat" class="pv-chat-conatiner">'+
'    </div>'+
'    <div class="pv-input-container">'+
'        <textarea id="pv-input" type="text"></textarea>'+
'    </div>'+
'</div>'+
'<script>'+
'    </div>';
}
var pv_onLoad = function() {
    var pv_addMessage = function(msg){
        var cont = document.getElementById("pv-chat");
        var elm = document.createElement("div");
        elm.class="pv-chat-msg";
        elm.innerHTML='<span class="pv-msg-username" style="color:' +
            msg["color"] + '">' + msg["username"] +
            ':</span> <span class="pv-msg-body">' + msg["body"] + '</span>';
        console.log('msg added');
        console.log(elm);
        cont.appendChild(elm);
        cont.scrollTop = cont.scrollHeight;
    };
    var pv_onDisconnect = function() {
        console.log("disconnected");
        document.getElementById('pv-connection-light').style['background-color']
            = '#F00';
        document.getElementById('pv-connection-light').style['box-shadow']
            = '0px 0px 2px 2px #F00';
        
    }
    var pv_onConnect = function() {
        console.log("connected");
        document.getElementById('pv-connection-light').style['background-color']
            = '#0F0';
        document.getElementById('pv-connection-light').style['box-shadow']
            = '0px 0px 2px 2px #0F0';
    }
    AMQPWebsocket({onmessage:pv_addMessage,onopen:pv_onConnect,onerror:pv_onDisconnect,onclose:pv_onDisconnect}); 
    document.getElementById("pv-pin").addEventListener("click",function(){
        var box = document.getElementById("pv-box");
        if (box.style.display ==="none") {
            document.getElementById("pv-box").style["visibility"]="visible";
            document.getElementById("pv-box").style["display"]="block";
        } else {
            document.getElementById("pv-box").style["visibility"]="hidden";
            document.getElementById("pv-box").style["display"]="none";
        }
    });
    document.getElementById("pv-input").addEventListener("keypress",function (event){
        evt = window.event || evt;
        var key = evt.which || evt.keyCode;
        if (key == 13) {
            var msg = document.getElementById("pv-input").value;
            window.pv_amqp_ws.send(window.pv_username,msg,"test","",window.pv_color);
            var msg = document.getElementById("pv-input").value = "";
            if (window.event) {
                window.event.returnValue = false;
            } else {
                evt.preventDefault();
            }
        }
        return true;
    });
}
var head= document.getElementsByTagName('head')[0];
var script= document.createElement('script');
script.type= 'text/javascript';
script.src= '/static/js/amqp.js';
head.appendChild(script);
var body = document.getElementsByTagName('body')[0];
var peerview = document.createElement('div');
peerview.innerHTML = generate_html();
body.onreadystatechange = pv_onLoad;
body.onload = pv_onLoad;
body.appendChild(peerview);
