
function show_load_diagnostics(){
    console.log("Show it...");
    
    var time_log_html = "No timelog created."
    if(typeof(time_log) != "undefined" && time_log.length > 0){
        time_log_html = ""
        
        time_log_html += "<div class='flex bbottom'>";
        time_log_html += "<div class='col-9-6'><span class='font-15 bold'>Task</span></div>";
        time_log_html += "<div class='col-3-6 right'><span class='font-15 bold'>Duration</span></div>";
        time_log_html += "</div>";
        
        for(var a = 0;a<time_log.length-1;a++){
            var log = time_log[a];
            time_log_html += "<div class='flex table-row'>";
            time_log_html += "<div class='col-9-6'><span class='font-15'>" + log.tag + "</span></div>";
            time_log_html += "<div class='col-3-6 right'><span class='font-15'>" + log.duration_str + "</span></div>";
            time_log_html += "</div>";
        }
        var log = time_log[time_log.length-1];
        time_log_html += "<div class='flex bold' style='border-top: solid 1px black;'>";
        time_log_html += "<div class='col-9-6'><span class='font-15 bold'>Total</span></div>";
        time_log_html += "<div class='col-3-6 right'><span class='font-15 bold'>" + log.duration_str + "</span></div>";
        time_log_html += "</div>";
        
    }
    html = '';
        html += '<div class="col-12 flex">';
            html += '<div class="col-3-1"></div>';
            html += '<div class="col-6-10 popup-content">';
            html += time_log_html;
           
            html += '<div class="col-12 centered" style="padding-top:30px;"><button class="action-button" onclick="hide_overlay();" class="close"><span class="">Close</span></button></div>    ';
            html += '</div>';
            html += '<div class="col-3-1"></div>';
        html += '</div>';
    
    
    $("#overlay_panel").empty(); $("#overlay_panel").append(html); $("#overlay_panel").addClass("shown");
}

function hide_overlay(){
    $(".overlay").removeClass("shown");
}

function process_time_log(time_log){
    var total = 0;
    for(var a = 0;a<time_log.length;a++){
        var log = time_log[a];
        if(!('duration' in log)){
            log.duration = log.end - log.start;
        }
        total += log.duration;
    }    
    for(var a = 0;a<time_log.length;a++){
        var log = time_log[a];
        
        
        if(log.duration > 5000){ dur = Math.round(log.duration/1000.0*10.0)/10.0 + "s"; }
        else if(log.duration > 1000){ dur = Math.round(log.duration/1000.0*100.0)/100.0 + "s"; }
        else{ dur = log.duration + "ms"; }
        
        log.duration_str = dur;
    }
    
    time_log.push({'tag': "Total", 'duration_str': total/1000.0 + "s"});
    
    
}

function display_notifications(notifications){
    console.log(notifications);
    var allow_close = true;
    var elem = $("#banner"); elem.empty();
    elem.css("background-color", "#EFE").css("text-align", "left");
    var n = null;
    for(var a = 0;a<notifications.length;a++){
        n = notifications[a];
        if(n.persistent){ allow_close = false; }
        
        if('nospan' in n && n.nospan==1){
            n.final_html = "<div class='no-padding'>" + n.html + "</div>";
        }
        else{
            n.final_html = "<div class='no-padding'><span style='padding-left:10px;' class='font-12'>" + n.html + "</span></div>";
        }
        elem.append(n.final_html);
    }
    
    if(allow_close){
        var close_html = "";
        close_html = "<a class='font-12 text-button' onclick='$(\"#banner\").addClass(\"closed\");'>CLOSE</a>";
        close_html = "<div class='no-padding right pointer'><span class='pointer' style='padding-right:20px;'>" + close_html + "</span></div>";
        elem.append(close_html);
    }
}

function finish_load(notifications){
    
    if(notifications.length > 0){ display_notifications(notifications); }

    // Change color of main logo; this will be used for the testing script to confirm that all JS was run successfully
    if($("#main_logo").css("color") == "rgb(51, 51, 51)"){
        document.getElementById("main_logo").style.color = "rgb(51, 51, 52)";
    }
    else if($("#main_logo").css("color") == "rgb(255, 255, 255)"){
        document.getElementById("main_logo").style.color = "rgb(255, 254, 254)";
    }
}

function show_explanation(tags){
    var tags = tags.split("|");
    if(tags.length != 2){
        exp = 'Oops...|There should be something here, but there isn\'t. Apologies.'
    }
    else if(typeof explanations == "undefined"){
        exp = 'Oops...|There should be something here, but there isn\'t. Apologies.'
    }
    else if(explanations == null){
        exp = 'Oops...|There should be something here, but there isn\'t. Apologies.'
    }
    else{
        exp = 'Oops...|There should be something here, but there isn\'t. Apologies.'
        for(var a = 0;a<explanations.length;a++){
            var explanation = explanations[a];
            console.log(explanation.html_page , tags[0] , explanation.tag , tags[1]);
            if(explanation.html_page == tags[0] && explanation.tag == tags[1]){
                exp = explanation.header_text + "|" + explanation.explanation_html_BR;
            }
        }
    }    
        
    exp_html = "<div class='col-12 flex'><div class='col-10'><span class='font-36 bold contents'>" + exp.split("|")[0] + "</span></div>";
    exp_html += "<div class='col-2 right'><img onclick='hide_overlay();' src='/static/img/Close24.png' /></div></div>";
    exp_html += "<div class='col-12 exp-scroll'><span class='font-15 contents'>" + exp.split("|")[1] + "</span></div>";
    
    html = '';
        html += '<div class="flex" style="max-height:450px; margin:5px;">';
            html += '<div class="col-1"></div>';
            html += '<div class="col-10 popup-content">';
            html += exp_html;
           
            html += '<div class="col-12 centered" style="padding-top:30px;"><button class="action-button" onclick="hide_overlay();" class="close"><span class="">Close</span></button></div>    ';
            html += '</div>';
            html += '<div class="col-1"></div>';
        html += '</div>';
    
    
    $("#overlay_panel").empty(); $("#overlay_panel").append(html); $("#overlay_panel").addClass("shown");
}

function set_panel(val){
    panel = val;
    $(".panel_tag").removeClass("tag-on").addClass("tag-off"); 
    $("#" + val + "_view_tag").removeClass("tag-off").addClass("tag-on"); 

    $(".panel").removeClass("visible").addClass("hidden"); 
    $("#" + val + "_view").removeClass("hidden").addClass("visible"); 
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
            html += "<input id='edit_value_" + p.key + "' class='large' type=text name='" + p.key + "' value='" + p.value + "' />";
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
  
