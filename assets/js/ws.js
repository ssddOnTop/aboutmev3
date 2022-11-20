
let ws = new WebSocket('wss://api.mindupstream.com/latest');
let itemjson = '[]';
ws.onmessage = function (evt){
    if(checkLoaded()){
        createPost(evt.data);
    }else {
        itemjson = evt.data;
    }
}

window.addEventListener('load', function() {
    createPost(itemjson);
}, true);

function checkLoaded() {
    return document. readyState === "complete" || document. readyState === 'interactive';
}