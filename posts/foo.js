function changeDocTitle(title){
    document.title = title;
}

function changePathBack(){
    window.history.back();
}

function changePathFwd(page, path){
    window.history.pushState(page, null, currentLocation() + '/'+ path);
}

function currentLocation(){
    console.log(window.location.pathname)
    return window.location.href;
}