

function finish_load(){
    
    console.log("Finish load...")
    // Change color of main logo; this will be used for the testing script to confirm that all JS was run successfully
    if($("#main_logo").css("color") == "rgb(51, 51, 51)"){
        document.getElementById("main_logo").style.color = "rgb(51, 51, 52)";
    }
    else if($("#main_logo").css("color") == "rgb(255, 255, 255)"){
        document.getElementById("main_logo").style.color = "rgb(255, 254, 254)";
    }
}
function menu_toggle(only_if_open=false){
    tags = {'dtop': 1, 'mob': 1};
    for(t in tags){
        var elem_name = 'menu_modal_' + t;
        if(document.getElementById(elem_name) != null){
            var cur = document.getElementById(elem_name).style.display;
            if(["none",""].indexOf(cur) > -1){
                if(!only_if_open){
                    document.getElementById(elem_name).style.display = "block";
                }
            }
            else{
                document.getElementById(elem_name).style.display = "none";    
            }
        }
    }
}



    
function populate_preferences(preferences){
    var elem = $("#top_container"); elem.empty(); var html = "";
    html += "<FORM action='/preferences' method=POST>";
    for(var a = 0;a<preferences.length;a++){
        var p = preferences[a];
        html += "<div id='preference_group_" + p.key + "' class='col-12 flex table-row'>";
        
        html += "<div class='col-6'><span class='font-15'>" + p.dtop_display + "</span></div>";
        html += "<div class='col-6 right'>";
        
        if(p.element == "select"){
            html += "<select id='edit_value_" + p.key + "' name='" + p.key + "'>";
            for(var b = 0;b<p.options.length;b++){
                var opt = p.options[b];
                html += "<option value='" + opt.value + "' " + opt.selected + ">" + opt.display + "</option>";
            }
            html += "</select>";
        }
        else if(p.element == "text"){
            html += "<input id='edit_value_" + p.key + "' class='medium' type=text name='" + p.key + "' value='" + p.value + "' />";
        }
        
        html += "</div>";
        
        html += "</div>";
        
    }
    
    if(misc.error != null){ html += "<div class='col-12 error centered'><span class='error' >" + misc.error + "</span></div>";    }
    if(misc.msg != null){ html += "<div class='col-12 centered'><span class='msg' style='color:blue;' >" + misc.msg + "</span></div>";    }
    
    html += "<div class='col-12 action-button right'>";
    html += "<button class='action-button' type=submit name='action' id='submit_me' value='edit_preferences'>SAVE</button>";
    html += "</div>";
    html += "</FORM>";
    elem.append(html);
}
function populate_profile(profile){
    var elem = $("#top_container"); elem.empty(); var html = "";
    html += "<FORM action='/profile' method=POST>";
    for(var a = 0;a<profile.length;a++){
        var p = profile[a];
        html += "<div id='profile_group_" + p.key + "' class='col-12 flex'>";
        
        html += "<div class='col-6'><span class='font-15'><span class='dtop'>" + p.dtop_display + "</span><span class='mob'>" + p.mob_display + "</span></span></div>";
        html += "<div class='col-6 right'>";
        
        if(p.element == "select"){
            html += "<select id='edit_value_" + p.key + "' name='" + p.key + "'>";
            for(var b = 0;b<p.options.length;b++){
                var opt = p.options[b];
                html += "<option value='" + opt.value + "' " + opt.selected + ">" + opt.display + "</option>";
            }
            html += "</select>";
        }
        else if(p.element == "text"){
            html += "<input id='edit_value_" + p.key + "' class='medium' type=text name='" + p.key + "' value='" + p.value + "' />";
        }
        
        html += "</div>";
        
        html += "</div>";
        
    }
    
    if(misc.error != null){ html += "<div class='col-12 error centered'><span class='error' >" + misc.error + "</span></div>";    }
    if(misc.msg != null){ html += "<div class='col-12 centered'><span class='msg' style='color:blue;' >" + misc.msg + "</span></div>";    }
    
    
    html += "<div class='col-12 action-button right'>";
    html += "<button class='action-button' type=submit name='action' id='submit_me' value='edit_profile'>SAVE</button>";
    html += "</div>";
    html += "</FORM>";
    elem.append(html);
}
    