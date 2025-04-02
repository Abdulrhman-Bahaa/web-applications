

var goals  = ['','','','','','','','','','','','','',''];
var buttons = [];
for (i = 0; i < 14; i++) {
    if (getCookie(`in${i}`)  != null ) {
        goals[i] = (getCookie(`in${i}`));
    }
   
    
    if (getCookie(`cbx${i}`)  != null ) {
        buttons[i] = "checked";
    } 

    let td = document.getElementById(`g${i}`);
    td.innerHTML = `<input type='text' autocomplete='off'  id='in${i}' value='${goals[i]}' placeholder='${defaultGoals[i]}'  class='form-control js-goals-text-input' >
                    <input value='${goals[i]}' class='inp-cbx js-goals-btn-input' id='cbx${i}'   type='checkbox' ${buttons[i]} style='display: none'/> 
                    <label class='cbx' for='cbx${i}'><span><svg width='200px' height='18px' viewbox='-65 1 12 18'><polyline points='1.5 6 4.5 9 10.5 2'></polyline></svg></span></label>`;   
}





















