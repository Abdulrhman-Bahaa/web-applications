

goalsTextInput.forEach(function(element ) {
    element.addEventListener("input",function() {
        var name = this.id;
        document.body.addEventListener("click",function(){
            var v = element.value;
            document.cookie = `${name}=${v}; expires= ${nextSunday} 00:01:00 UTC`;
            location.reload();
        });
    });
});


goalsBtnInput.forEach(function(element) {
    element.addEventListener("click",function() {   
        
        if (getCookie(`${this.id}`)  === null ) {
            document.cookie = `${this.id}="checked"; expires= ${nextSunday} 00:00:00 UTC`;
        }  
        else { 
            deleteCookie(`${this.id}`, path, domain );
        }
                
    });
});


hoursRangeInput.forEach(function(element) {
    element.addEventListener("change",function() {   
        var v = this.value; 
        document.cookie = `${this.id}=${v}; expires= ${nextSunday} 00:00:00 UTC`;
                
    });
});


overlay.addEventListener("click",function() { 
    stage.style.display = 'none';
    card.style.height = '80%' ;
    habitsTable.style.top = '50%';
    stage.appendChild(toggle1);
    allContainer.appendChild(habitsContainer);
    allContainer.appendChild(defaultValuesContainer);
    allContainer.appendChild(summaryContainer);
});


firstSubmitBtns.forEach(function(element) {
    if (getCookie(`${element.id}`)) {
        element.disabled = true;
    }
});


colorChanger.addEventListener("input",function() {
    color = this.value;
    if (getCookie('dark')) {
        document.cookie = `darkColor=${color}; expires= ${nextSunday} 00:00:00 UTC`;      
    }
    else {
        document.cookie = `lightColor=${color}; expires= ${nextSunday} 00:00:00 UTC`;
    }
    htmlTag.style.cssText = `--main-color : ${color};`;
})


daysTd.forEach(function(element) {
    var id = element.id.substring(3);
    if (element.innerHTML == currentDay) {
        document.getElementById(`currentDay${id}`).style.display = 'block';    
    }
});


if (screen.width == 1280) {
    document.querySelectorAll('td svg').forEach(function(element) {
                element.setAttribute("viewBox", "-40 1 12 18"); 
                element.setAttribute("width", "120px"); 
    }); 
}











