'use strict';

// navbar variables
const nav = document.querySelector('.mobile-nav');
const navMenuBtn = document.querySelector('.nav-menu-btn');
const navCloseBtn = document.querySelector('.nav-close-btn');


// navToggle function
const navToggleFunc = function () { nav.classList.toggle('active'); }

navMenuBtn.addEventListener('click', navToggleFunc);
navCloseBtn.addEventListener('click', navToggleFunc);



// theme toggle variables
const themeBtn = document.querySelectorAll('.theme-btn');


for (let i = 0; i < themeBtn.length; i++) {

  themeBtn[i].addEventListener('click', function () {
    // toggle `light-theme` & `dark-theme` class from `body`
    // when clicked `theme-btn`
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');


    for (let i = 0; i < themeBtn.length; i++) {

      // When the `theme-btn` is clicked,
      // it toggles classes between `light` & `dark` for all `theme-btn`.
      themeBtn[i].classList.toggle('dark');
      themeBtn[i].classList.toggle('light');
    }

  })

}

let btn = document.getElementById('loadmore');

btn.onclick = function (){
  window.open('https://www.mindupstream.com/log', "_blank");
}

/*
const ul = document.getElementById("rec_blogs");

function createPost(blogArr){
  //heading, image, alt, tag, shortDesc, linkx
  let json = JSON.parse(blogArr);
  for (const j in json) {
    let li = document.createElement("li");
    li.setAttribute("class", "blog-card");
    let d1 = document.createElement("div");
    d1.setAttribute("class", "blog-card-banner");
    let i1 = document.createElement("img");
    i1.src = j.image;
    i1.alt = j.alt;
    i1.width = 250;
    i1.setAttribute("class", "blog-banner-img");

    d1.appendChild(i1);
    li.appendChild(d1);

    let d2 = document.createElement("div");
    d2.setAttribute("class", "blog-content-wrapper");

    let tagBtn = document.createElement("button");
    tagBtn.setAttribute("class", "blog-topic text-tiny");
    tagBtn.textContent = j.tag;

    let h3 = document.createElement('h3');
    let a = document.createElement("a");

    a.href = j.linkx;
    a.setAttribute("class", "h3");
    a.textContent = j.heading;

    h3.appendChild(a);

    let p = document.createElement("p");
    p.setAttribute("class","blog-text");
    p.textContent = j.shortDesc;

    d2.appendChild(tagBtn);
    d2.appendChild(h3);
    d2.appendChild(p);

    li.appendChild(d2);

    ul.appendChild(li);

  }
}*/
