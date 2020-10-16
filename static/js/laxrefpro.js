
function show_load_diagnostics(){
    
    var time_log_html = "No timelog created."
    if(typeof(time_log) != "undefined" && time_log.length > 0){
        
        var total = 0;
        for(var a = 0;a<time_log.length;a++){
            var log = time_log[a];
            log.duration = log.end - log.start;
            total += log.duration;
        }    
        for(var a = 0;a<time_log.length;a++){
            var log = time_log[a];
            
            if(log.duration > 5000){ dur = Math.round(log.duration/1000.0*10.0)/10.0 + "s"; }
            else if(log.duration > 1000){ dur = Math.round(log.duration/1000.0*100.0)/100.0 + "s"; }
            else{ dur = log.duration + "ms"; }
            
            log.duration_str = dur;
        }
        
        
        time_log_html = ""
        
        time_log_html += "<div class='flex bbottom'>";
        time_log_html += "<div class='col-9-6'><span class='font-15 bold'>Task</span></div>";
        time_log_html += "<div class='col-3-6 right'><span class='font-15 bold'>Duration</span></div>";
        time_log_html += "</div>";
        
        for(var a = 0;a<time_log.length;a++){
            var log = time_log[a];
            //console.log(log);
            time_log_html += "<div class='flex table-row'>";
            time_log_html += "<div class='col-9-6'><span class='font-15'>" + log.tag + "</span></div>";
            time_log_html += "<div class='col-3-6 right'><span class='font-15'>" + log.duration_str + "</span></div>";
            time_log_html += "</div>";
        }
        total = {'tag': "Total", 'duration_str': total/1000.0 + "s"};
        
        var log = time_log[time_log.length-1];
        time_log_html += "<div class='flex bold' style='border-top: solid 1px black;'>";
        time_log_html += "<div class='col-9-6'><span class='font-15 bold'>Total</span></div>";
        time_log_html += "<div class='col-3-6 right'><span class='font-15 bold'>" + total.duration_str + "</span></div>";
        time_log_html += "</div>";
        
    }
    
    
    html = '';
    html += '<div class="flex" style="max-height:450px; margin:5px;">';
        html += '<div class="col-1"></div>';
        html += '<div class="col-10 popup-content">';
        html += time_log_html;
       
        
        html += '<div class="col-12 centered" style="padding-top:15px;"><button class="action-button" onclick="hide_overlay();" class="close"><span class="">Close</span></button></div>    ';
        html += '</div>';
        html += '<div class="col-1"></div>';
    html += '</div>';

    
    
    
    $("#overlay_panel").empty(); $("#overlay_panel").append(html); $("#overlay_panel").addClass("shown");
}

function d3toggle_click_orig(){
    
    toggle_obj = d3.select(this);
    id = toggle_obj.attr('id');
    balls_class = "." + toggle_obj.attr('class').split(" ").filter(r => r != "blue").join(".");
    background_class = balls_class.replace("ball", "background");
    
    tmp = id.replace("-toggle-ball", "") + "." + "toggle-ball";

    balls = d3.selectAll(balls_class);
    backgrounds = d3.selectAll(background_class);
    
    is_initial = parseInt(toggle_obj.attr("nonce"));
    console.log("Toggle: "+ id + "  Class: "+ balls_class + "    initial: " + is_initial);
    if(is_initial){
        $(balls_class).addClass("blue"); $(background_class).removeClass("blue");
    }
    else{
        $(background_class).addClass("blue"); $(balls_class).removeClass("blue");
    }
    direction = is_initial ? -1 : 1;
    balls.attr("cx", function(d){ return parseFloat(d3.select(this).attr("cx")) + direction* (parseFloat(toggle_obj.attr("r"))*2 + 2); } );
    
    if(id == "ranks_mob_calculation"){ 
        if(is_initial){ toggle_radio("off_radio2 offensive_calculation_radio", "off_radio2"); }
        else{ toggle_radio("off_radio1 offensive_calculation_radio", "off_radio1"); }
    }
    if(id == "ranks_mob_peers"){ 
        if(is_initial){ toggle_radio("off_radio3 offensive_peers_radio", "off_radio3mob"); }
        else{ toggle_radio("off_radio4 offensive_peers_radio", "off_radio4mob"); }
    }
    
    balls.attr("nonce", is_initial ? 0 : 1);
    
    
} 
            
function toggler(what=null){

    if(what == null){ // If the thing that was clicked is a d3 toggle object
        this_class = d3.select(this).attr("class").split(" ").filter(r => ['set', 'toggle-ball'].indexOf(r) == -1);       
    }
    else{ // If the thing that was clicked is a basic old HTML input
        this_class = what.classList.value.split(" ");
    }
    
    // If we got a class list we weren't expecting, report it and exit
    if(this_class == []){ report_js_visualization_issue(misc.target_template + "|" + 'toggler' + "|" + misc.nhca); return; }
    this_class = this_class[0];
    
    //console.log("this_class: " + this_class);
    

    // Select the toggles and input.radios that need to be processed
    balls = d3.selectAll(".toggle-ball." + this_class);
    backgrounds = d3.selectAll(".toggle-background." + this_class);
    radios = $("input." + this_class);

    
    // Toggle & move the toggle balls and identify whether the initial option is selected or not
    is_not_set = null;
    balls.each(function(d, i){ 
        obj = d3.select(this); 
        direction = parseInt(obj.attr("nonce")) ? -1 : 1;
        obj.attr("nonce", parseInt(obj.attr("nonce")) ? 0 : 1);
        
        if(i == 0){ is_not_set = parseInt(obj.attr("nonce")); }
        
        cur_class = obj.attr("class");
        if(cur_class.indexOf(" set") == -1){ obj.attr("class", cur_class + " set"); }
        else{ obj.attr("class", cur_class.replace(" set", "")); }
        obj.attr("cx", parseFloat(obj.attr("cx")) + direction* (parseFloat(obj.attr("r"))*2 + 2) );
    
    });
    
    // Switch the relevant backgrounds to whatever state they need to be moved to
    backgrounds.each(function(d){ 
        obj = d3.select(this);
        cur_class = obj.attr("class");
        if(cur_class.indexOf(" set" ) == -1){ obj.attr("class", cur_class + " set"); }
        else{ obj.attr("class", cur_class.replace(" set", "")); }
    });
    
    // Unless the radio input has the same name as the one clicked, switch its state
    radios.each(function(d, i){ if(what == null || what.name != $(this).prop("name")){ cur = $(this).prop("checked"); $(this).prop("checked", !cur); } });
    
    // Do whatever actual JS code is suggested by the object clicked
    if(this_class == "offensive_calculation_radio"){
        calc_specs.offense.calculation = is_not_set ? "adjusted" : "raw";
        display_primary_unit("offense", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'offensive_ranks_calculation', calc_specs.offense.calculation].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    if(this_class == "defensive_calculation_radio"){
        calc_specs.defense.calculation = is_not_set ? "adjusted" : "raw";
        display_primary_unit("defense", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'defensive_ranks_calculation', calc_specs.defense.calculation].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    if(this_class == "faceoffs_calculation_radio"){
        calc_specs.faceoffs.calculation = is_not_set ? "adjusted" : "raw";
        display_faceoffs("faceoffs", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'faceoffs_ranks_calculation', calc_specs.faceoffs.calculation].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    if(this_class == "goalkeepers_calculation_radio"){
        calc_specs.goalkeepers.calculation = is_not_set ? "adjusted" : "raw";
        display_goalkeepers("goalkeepers", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'goalkeepers_ranks_calculation', calc_specs.goalkeepers.calculation].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    
    
    if(this_class == "offensive_peers_radio"){
        calc_specs.offense.peers = is_not_set ? "conference" : "league";
        display_primary_unit("offense", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'offensive_ranks_peers', calc_specs.offense.peers].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    if(this_class == "defensive_peers_radio"){
        calc_specs.defense.peers = is_not_set ? "conference" : "league";
        display_primary_unit("defense", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'defensive_ranks_peers', calc_specs.defense.peers].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    if(this_class == "faceoffs_peers_radio"){
        calc_specs.faceoffs.peers = is_not_set ? "conference" : "league";
        display_faceoffs("faceoffs", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'faceoffs_ranks_peers', calc_specs.faceoffs.peers].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    if(this_class == "goalkeepers_peers_radio"){
        calc_specs.goalkeepers.peers = is_not_set ? "conference" : "league";
        display_goalkeepers("goalkeepers", null);
        logger_str = ["team_my_stats.html", misc.nhca, 'goalkeepers_ranks_peers', calc_specs.goalkeepers.peers].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }
    
    
} 
            

    
function toggle_radio(this_class, this_id){
    console.log("Set true: " + "." + this_class.replace(" ", "."));
    $('.' + this_class.split(" ")[1]).prop('checked', false);
    $("." + this_class.replace(" ", ".")).prop('checked', true);
    
    if(this_class.split(" ")[1] == "offensive_calculation_radio"){
        
        if(['off_radio1', 'off_radio1mob', 'off_radio1a', 'off_radio1amob'].indexOf(this_id) > -1){ calc_specs[unit].calculation = "raw"; }
        else{ calc_specs[unit].calculation = "adjusted"; }
        display_primary_unit("offense", "offensive_ranks");
        logger_str = ["team_my_stats.html", misc.nhca, 'offensive_ranks_calculation', calc_specs[unit].calculation].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
        
    }
    if(this_class.split(" ")[1] == "offensive_peers_radio"){
        
        if(['off_radio3', 'off_radio3mob', 'off_radio3a', 'off_radio3amob'].indexOf(this_id) > -1){ calc_specs[unit].peers = "league"; }
        else{ calc_specs[unit].peers = "conference"; }
    
        display_primary_unit("offense", "offensive_ranks");
        logger_str = ["team_my_stats.html", misc.nhca, 'offensive_ranks_peers', calc_specs[unit].peers].join("|");
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
    }    
}

function parse_misc(output){
    
    return output;
}
function show_console(){
    console.log("Show it...");
    
    var time_log_html = "No timelog created."
    if(typeof(console_log) != "undefined" && console_log.length > 0){
        time_log_html = ""
        
        time_log_html += "<div class='flex bbottom'>";
        time_log_html += "<div class='col-9-6'><span class='font-15 bold'>Task</span></div>";
        time_log_html += "<div class='col-3-6 right'><span class='font-15 bold'>Duration</span></div>";
        time_log_html += "</div>";
        
        for(var a = 0;a<console_log.length-1;a++){
            var log = console_log[a];
            time_log_html += "<div class='flex table-row'>";
            time_log_html += "<div class='col-12'><span class='font-15'>" + log.msg + "</span></div>";
            time_log_html += "</div>";
        }
        
    }
    
    
    html = '';
    html += '<div class="flex" style="max-height:450px; margin:5px;">';
        html += '<div class="col-1"></div>';
        html += '<div class="col-10 popup-content exp-scroll">';
        html += time_log_html;
       
        
        html += '<div class="col-12 centered" style="padding-top:15px;"><button class="action-button" onclick="hide_overlay();" class="close"><span class="">Close</span></button></div>    ';
        html += '</div>';
        html += '<div class="col-1"></div>';
    html += '</div>';

    
    
    
    $("#overlay_panel").empty(); $("#overlay_panel").append(html); $("#overlay_panel").addClass("shown");
}

function hide_overlay(){
    $(".overlay").removeClass("shown");
}

Date.prototype.addDays = function(days) {
    var date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
}

function days_to_date(days, fmt, since=new Date(2015, 0, 1)){
    var s = null;
    try{
        var dt = since.addDays(days);
        
        var s = null;
        if(fmt == "%b %d %Y"){
            s = dt.toString().substring(4);
            s = s.substring(0, 11);
            s = s.substring(0, 6) + ", " + s.substring(7);
            
        }
        else if(fmt == "%b %Y"){
            s = dt.toString().substring(4);
            s = s.substring(0, 4) + s.substring(7, 11);
            
        }
        else if(fmt == '%b %d \'%y'){
            s = dt.toString().substring(4);
            s = s.substring(0, 11);
            s = s.substring(0, 6) + " '" + s.substring(9);
            
        }
        s = s.replace(" 0", " ");

    }
    catch(err){ console_log.push({'msg': "Error converting days_to_date to string"}); }
    return s;
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

function choose_left_menu_item(id){
    id = id.replace("_menu_item", "");
    console.log("Enable " + id);
    
    $(".left-menu-item").removeClass("active");
    $(".right-content-panel").removeClass("active");
    $("#" + id + "_menu_item").addClass("active");
    $("#" + id + "_panel").addClass("active");
    $("#top_menu_select").val(id);
    redraw(id);
    
}

function display_notifications(notifications){
    var elem = $("#banner"); elem.empty();
    
    if(typeof notifications != "undefined" && notifications != null && notifications.length > 0){
        var allow_close = true;
        
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
    else{
        elem.css("display", "none");
    }
}

function finish_load(notifications){
    // Stop event propagation for the appropriate classes
    $( "#threedot" ).click(function( event ) { event.stopPropagation(); menu_toggle(); });
    $( "#personicon" ).click(function( event ) { event.stopPropagation(); menu_toggle(); });
    $(".icon-15.explanation").click(function( event ) {  event.stopPropagation(); show_explanation(this.getAttribute("value")); });
    $(".icon-15.settings").click(function( event ) {  event.stopPropagation(); });
    $(".icon-15.toggle").click(function( event ) {  event.stopPropagation(); });
    $(".dashboard-tile-content").click(function( event ) { event.stopPropagation(); });
    
    // If there are any notifications, display them in the banner /notifications bar
    console_log.push({'msg': 'Start display_notifications...'});
    display_notifications(notifications);

    // Set the current status of any settings objects that the user previously changed
    console_log.push({'msg': 'Start apply_user_settings...'});
    apply_user_settings();
    
    
    
    // Change color of main logo; this will be used for the testing script to confirm that all JS was run successfully
    if($("#main_logo").css("color") == "rgb(51, 51, 51)"){
        document.getElementById("main_logo").style.color = "rgb(51, 51, 52)";
    }
    else if($("#main_logo").css("color") == "rgb(255, 255, 255)"){
        document.getElementById("main_logo").style.color = "rgb(255, 254, 254)";
    }
}

function explanation_feedback(s){
    document.getElementById('pixel').src = "/logger-explanationFeedback?c=" + s;
    $(".feedback-request").addClass("hidden");
    $(".feedback-request-thanks").removeClass("hidden");
}

function report_js_visualization_issue(s){
    document.getElementById('pixel').src = "/logger-jsVisualizationFail?c=" + s;
}

function show_explanation(tags){
    var feedback_yes = null; var feedback_no = null; var logger_str = null;
    $(".feedback-request").removeClass("hidden");
    $(".feedback-request-thanks").addClass("hidden");
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
            //console.log(explanation.html_page , tags[0] , explanation.tag , tags[1]);
            if(explanation.html_page == tags[0] && explanation.tag == tags[1]){
                exp = explanation.header_text + "|" + explanation.explanation_html_BR;
                logger_str = [tags[0], tags[1], misc.nhca].join("|");
                feedback_no = logger_str + "|0";
                feedback_yes = logger_str + "|1";                
                document.getElementById('pixel').src = "/logger-explanationOpen?c=" + logger_str;
                break;
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
           
            if(feedback_yes != null){
                html += "<div class='feedback-request col-12 right' style='padding-top:15px;'><span class='font-12'>Was this helpful?</span><span onclick='explanation_feedback(\"" + feedback_yes + "\")' class='mouseover-link font-12'>Yes</span><span onclick='explanation_feedback(\"" + feedback_no + "\")' class='mouseover-link font-12 '>No</span></div>    ";
                html += "<div class='feedback-request-thanks hidden col-12 right' style='padding-top:15px;'><span class='font-12 contents' style='color:blue;'>Thank you. Feedback is greatly appreciated.</span></div>    ";
            }
            
            html += '<div class="col-12 centered" style="padding-top:15px;"><button class="action-button" onclick="hide_overlay();" class="close"><span class="">Close</span></button></div>    ';
            html += '</div>';
            html += '<div class="col-1"></div>';
        html += '</div>';
    
    
    $("#overlay_panel").empty(); $("#overlay_panel").append(html); $("#overlay_panel").addClass("shown");
}

function drill_down_header(id, toggle=false){
    var elem = $("#" + id);
    var route = elem[0].getAttribute("route").split("|");
    
    if(on_mobile || toggle){
        toggle_tile_visibility(route[1]);
    }
    else{
        
        var ddf = $("#drill_down_form");
        var active_element = $("#active_element");
    
        active_element.attr("value", route[1]);
        ddf.attr("action", "/" + route[0]);
        ddf.submit();
    }
    
}

function drill_down_body(id){
    var elem = $("#" + id);
    var route = elem[0].getAttribute("route").split("|");
    
    var ddf = $("#drill_down_form");
    var active_element = $("#active_element");

    active_element.attr("value", route[1]);
    ddf.attr("action", "/" + route[0]);
    ddf.submit();
    
}

function toggle_settings_bar(id){
    var bar = $("#" + id);
    var class_list = document.getElementById(id).className.split(/\s+/);
    
    if(class_list.indexOf("not-shown") == -1){ bar.addClass("not-shown"); }
    else{ bar.removeClass("not-shown"); }
    
}

function title(str) {
  return str.replace(
    /\w\S*/g,
    function(txt) {
      return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    }
  );
}

function update_settings(id, val){
    
    var bar = $("#settings-bar");
    var class_list = document.getElementById("settings-bar").className.split(/\s+/);
    if(id != null){
        console.log("Changed " + id + " to " + val + " on " + misc.target_template);
        
        
        logger_str = [misc.target_template, misc.nhca, id, val].join("|");
                
                
        document.getElementById('pixel').src = "/logger-editSettings?c=" + logger_str;
        
        if(is_default_settings(misc.target_template)){
            $("#settings-icon").attr("src", "/static/img/blue_gear15.png");
        }
        else{
            $("#settings-icon").attr("src", "/static/img/blue_gear15modified.png");
        }
        
        // Reload the page because the setting that was changed requires a full reload
        if(misc.refresh_settings_tags.indexOf(id) > -1){
            
            
            $("#refreshing-bar").removeClass("not-shown");
            $("#settings-bar").addClass("not-shown");
            
            setTimeout(() => {  window.location= "/" + misc.target_template.split(".html")[0]; }, 3000);

        }
        
    }
}

function zFormat(f, decimals=1){
    
      if(isNaN(f)){ return ""; }
      if(typeof f == "string"){ return f; }
      var debug = false;
      //if(f > 16.98 && f < 17){ debug = true; }
      if(debug){ console.log("\n\nReceived " + f + " w/ decimals = " + decimals); }
      
      var first = "";
      var second = "";
      var negative = true;
      if(f >= 0){ negative = false; }
      f = Math.abs(f);    
          
      var input = "" + f;
      
          
      var decimal = false;
      if(input.indexOf(".") > -1){
          decimal = true;
          first = input.split(".")[0];
          second = input.split(".")[1];
          if(debug){ console.log("SECOND A: " + second); }
          var mult = Math.pow(10,decimals);
          if(debug){ console.log("MULT: " + mult); }
          
          second_val = ("" + (Math.round(parseFloat("1." + second)*mult)/mult))
          
          if(second_val.indexOf(".") > -1){
              
              second = second_val.split(".")[1];
          }
          else{
              if(second_val == "2"){
                  if(debug){ console.log("Increment the first value because second_val == " + second_val); }
                  first = ("" + (1.0 + parseFloat(first)));
                  second = "";
                  for(var a = 0;a<decimals;a++){ second += "0"; }
              }
              else{
                  second = "";
                  for(var a = 0;a<decimals;a++){ second += "0"; }
              }
          }
          if(decimals == 0){ second = null; }
      }
      else{
          first = input;
          second = null;
          if(decimals > 0){
              second = "";
              for(var a = 0;a<decimals;a++){ second += "0"; }
          }
          second_val = null;
      }
      if(debug){ 
          console.log(" first: " + first + " len=" + first.length);
          console.log(" second: " + second);
          console.log(" second_val: " + second_val);
      }
      if(first.length > 3){
         var tmp = "";
         var printed = 0;
         for(var a = first.length-1;a>=0;a--){
             tmp = first.charAt(a) + tmp;
             printed += 1;
             if(printed % 3 == 0 && a > 0){
                 tmp = "," + tmp;
             }
             
             
         }
         if(debug){ console.log(" first becomes: " + tmp); }
         first = tmp;
      }
      
      
      var res = first;
      if(second != null){
          res += "." + second;
      }
      if(negative){
          //res = "(" + res + ")";
          res = "-" + res;
          
      }
      if(debug){ console.log("Returning " + res); }
      
      return res;
}


function apply_user_settings(){
    
    if(typeof user_obj == "undefined"){ return; }
    var is_default = true;
    console_log.push({'msg': 'apply_user_settings: load user settings...'});
    uos = user_obj.settings;
    console_log.push({'msg': 'apply_user_settings: load default settings...'});
    mds = misc.default_settings;
    
    html = "<span class='font-12'>MDS" + JSON.stringify(mds) + "</span>";
    html += "<span class='font-12'>UOS" + JSON.stringify(uos);
    html += "</span>";
    for(k in uos){
        if(uos[k].target_template == null || uos[k].target_template == misc.target_template){
            elem = document.getElementById(k);
            if(elem != null){
                if(uos[k].val != mds[k]){ is_default = false; }
                
                if(['general_focus_year'].indexOf(k) > -1){ // Select object
                    html += "<span class='font-13'>Set " + k + " select to " + uos[k].val + "</span>";
                    $("#" + k).val(uos[k].val);
                }
                else if([''].indexOf(k) > -1){ // Input object
                    
                }
                else if([''].indexOf(k) > -1){ // Radio/toggle object
                    
                }
                else if([''].indexOf(k) > -1){ // Checkbox object
                    
                }
                else if([''].indexOf(k) > -1){ // Slider object
                    
                }
            }
        }
        
        
        
    }
    
    
    
    console_log.push({'msg': 'apply_user_settings: adjust settings bar...'});
    if(document.getElementById("settings-bar") != null){
        var bar = $("#settings-bar");
        var class_list = document.getElementById("settings-bar").className.split(/\s+/);
        if(!is_default && class_list.indexOf("not-shown") > -1){ 
            bar.removeClass("not-shown"); 
            $("#settings-icon").attr("src", "/static/img/blue_gear15modified.png");
        }
    }
    
    
}


function is_default_settings(target_template){
    
    if(typeof user_obj == "undefined"){ console.log("1a"); return true; }
    if ( !('settings' in user_obj)){ console.log("2a"); return true; }
    if (user_obj.settings == null){ console.log("3a"); return true; }
    
    console.log("Target template: " + target_template);
    
    console.log("Misc default settings: ");
    console.log(misc.default_settings);
    
    console.log("User Obj settings: ");
    console.log(user_obj.settings);
    
    uos = user_obj.settings;
    mds = misc.default_settings;
    for(k in mds){
        console.log(k, mds[k], uos[k].val, mds[k]==uos[k].val);
        if(k in uos && uos[k].val != null && mds[k]!=uos[k].val ){ return false; }
    }
    return true;
}


function toggle_tile_visibility(id){
    var icon_elem = $("#" + id + "_helpicon");
    var filter_elem = $("#" + id + "_filtericon");
    var div_elem = $("#" + id + "_div");
    var img_elem = $("#" + id + "_img");
    var class_list = document.getElementById(id + "_div").className.split(/\s+/);
    
    var opening = false;
    if(class_list.indexOf("visible") == -1){
        icon_elem.addClass("icon-visible");
        filter_elem.addClass("icon-visible");
        div_elem.addClass("visible");
        img_elem.attr("src", "static/img/Gray_Minus150.png");
        opening = true;
    }
    else{
        filter_elem.removeClass("icon-visible");
        icon_elem.removeClass("icon-visible");
        div_elem.removeClass("visible");
        img_elem.attr("src", "static/img/Gray_Plus150.png");
    }
    
    if(opening){
        var window_height = $(window).height();
        var current_loc = $(document).scrollTop();
        var h = div_elem.height();
        var loc = div_elem.position().top;
        if(h + loc > window_height + current_loc){
            var offset = 0;
            while(h + loc > window_height + current_loc + offset){
                offset += 1;
            }
            
            
            $("html, body").animate({ scrollTop: (current_loc + offset + 30)}, "slow");
        }
    }
    redraw(id);
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
        else{
            console.log("Menu objects have not been created correctly...");
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
  
