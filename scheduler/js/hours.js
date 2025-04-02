

var hours  = ['0','0','0','0','0','0','0'];
for (i = 0; i < 7; i++) {
    if (getCookie(`ran${i}`)  != null ) {
        hours[i] = (getCookie(`ran${i}`));
    } 
    var ran = document.getElementById(`ran${i}`);
    ran.value = `${hours[i]}`;
}

