

function getCookie(name) {
    function escape(s) { return s.replace(/([.*+?\^$(){}|\[\]\/\\])/g, '\\$1'); }
    var match = document.cookie.match(RegExp('(?:^|;\\s*)' + escape(name) + '=([^;]*)'));
    return match ? match[1] : null;
}


function deleteCookie( name, path, domain ) {
    if ( getCookie( name ) ) {
    document.cookie = name + "=" +
    ((path) ? ";path="+path:"")+
    ((domain)?";domain="+domain:"") +
    ";expires=Thu, 01 Jan 1970 00:00:01 GMT";
    }
}


function theme() {
    if (themeSwitch.checked) {
        htmlTag.setAttribute("data-theme", "Dark");
        document.cookie = `dark=true; expires= ${nextSunday} 00:00:00 UTC`; 
        htmlTag.style.cssText = `--main-color : ${getCookie('darkColor')};`;
        colorChanger.value = getCookie('darkColor');

    }
    else {
        htmlTag.setAttribute("data-theme", "");
        deleteCookie( 'dark', path, domain );
        htmlTag.style.cssText = `--main-color : ${getCookie('lightColor')};`;
        colorChanger.value = getCookie('lightColor'); 
    }
}


function habitsFunction(s){
    stage.style.display = 'block';
    cardTitle.innerHTML = 'Habits';

    if (!stage.querySelector("#habits-container")) {
        allContainer.appendChild(toggle1);
        stage.appendChild(habitsContainer);
    }
    
    var id = s.substring(3);
    var state;
    var i = 0;

    habitsDataCell.forEach(function(element) {
        if (getCookie(`cbxx${id + i}`)  === null ){state = "";} else { state = "checked"}
        element.innerHTML = `<input class='inp-cbx' id='cbxx${id + i}' name='habits[]' value='${habits[i]}'  type='checkbox' ${state} style='display: none'/> 
                            <label class='cbx' for='cbxx${id + i}'><span><svg width='200px' height='18px' viewbox='-35 1 12 18'><polyline points='1.5 6 4.5 9 10.5 2'></polyline></svg></span></label>`;

        element.firstChild.addEventListener("click",function() {
            if (getCookie(`${this.id}`)  === null ) {
                 document.cookie = `${this.id}=checked; expires= ${nextSunday} 00:00:00 UTC`;
            }  
            else { 
                deleteCookie(`${this.id}`, path, domain );
            }
        });
       
        i++;

    });

    if (screen.width == 1280) {
  
        document.querySelectorAll('td svg').forEach(function(element) {
                    element.setAttribute("viewBox", "-40 1 12 18"); 
                    element.setAttribute("width", "120px"); 
        });
    }
}


function defaultValuesFunction(){
    stage.style.display = 'block';
    cardTitle.innerHTML = 'Default Values'

    if (!stage.querySelector("#default-values-container")) {
        stage.replaceChild(defaultValuesContainer, stage.childNodes[7]);
    }

    daySelectList.addEventListener("change",function(){
        var j = -1;
        for (i = 1;i <8;i++) {

            if(this.value == i) {            
                document.getElementById(`dv0`).value =  defaultGoals[i + j];
                document.getElementById(`dv1`).value =  defaultGoals[i + j + 1];
                document.getElementById(`dvr`).value = defaultHours[i - 1];
                break;
            }
            j++;
        }
    });
    defaultValuesChanger.addEventListener("click",function(){
        if (daySelectList.value == 0) {
            alert('Choose a day first');
        }
        else {
            defaultValuesForm.submit();
        }
    });
}


function summeryFunction(s) {
    var id = s.substring(3);
    habitsFunction(s);

    cardTitle.innerHTML = '';

   

    if (screen.width == 1280) {
        card.style.height = '10% ' ;
        summaryTable.style.left = '10%';
        summaryTable.style.top = '7%';
        habitsTable.style.top = '55%';
    }
    else {
         card.style.height = '90%' ;
         habitsTable.style.top = '58%';
    }

    if (!stage.querySelector("#summary-container")) {
        allContainer.appendChild(toggle0);
        card.appendChild(summaryContainer);
    }

    var day = days[id];
    dayText.innerHTML = day;

    var date = document.getElementById(`date${id}`).innerHTML;
    dateText.innerHTML = date;
    dateSubmit.value = date;

    var hours = document.getElementById(`ran${id}`).value;
    hoursText.innerHTML = hours;
    hoursSubmit.value = hours;

    var btn = document.getElementById(`cbx${id * 2}`); 
    if (btn.checked) {
        goalsText0.innerHTML = btn.value;
        goalsSubmit0.value = btn.value;
    }
    btn = document.getElementById(`cbx${id * 2 + 1}`);
    if (btn.checked) {
        goalsText1.innerHTML = btn.value;
        goalsSubmit1.value = btn.value;
    }

    secondSubmitBtn[0].addEventListener('click',function(){
        document.cookie = `${'sub' + id}=disabled; expires= ${nextSunday} 00:00:00 UTC`;
    });
}





















