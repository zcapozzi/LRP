


function menu_toggle(){
    tags = {'dtop': 1, 'mob': 1};
    for(t in tags){
        var elem_name = 'menu_modal_' + t;
        if(document.getElementById(elem_name) != null){
            var cur = document.getElementById(elem_name).style.display;
            if(["none",""].indexOf(cur) > -1){
                    document.getElementById(elem_name).style.display = "block";
            }
            else{
                    document.getElementById(elem_name).style.display = "none";    
            }
        }
    }
}