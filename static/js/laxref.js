var offense = true;
var stat_type = "rate";
var panel = "standard";
var sort_by = null;


var sort_tag = {'generic': null, 'by_opponents': 'cnt', 'standard': 'date', 'all_games': 'date'};
var sort_dir = {'generic': 'desc', 'by_opponents': 'desc', 'standard': 'desc', 'all_games': 'desc'};


// Generic

var generic_td = null;
function generic_sort_by_tag(tag){
    
    if(sort_tag.generic == tag){
        sort_dir.generic = ((sort_dir.generic == "desc") ? "asc" : "desc");
    }
    else{
        sort_tag.generic = tag;
        sort_dir.generic = "desc";
    }
    if (typeof generic_td.data[0][sort_tag.generic] == "object"){
        generic_td.data.sort(function(first, second) {
        
            if(sort_dir.generic == "desc"){
                return second[sort_tag.generic].val - first[sort_tag.generic].val;
            }
            else{
                return first[sort_tag.generic].val - second[sort_tag.generic].val;
            }
     
        });
    }
    else{
        generic_td.data.sort(function(first, second) {
        
            if(sort_dir.generic == "desc"){
                return second[sort_tag.generic] - first[sort_tag.generic];
            }
            else{
                return first[sort_tag.generic] - second[sort_tag.generic];
            }
     
        });
    }
    console.log("First element");
    console.log(generic_td.data[0]);
    console.log("sorted by " + sort_tag.generic + " " + sort_dir.generic);
    generic_create_table(generic_td);
}


function generic_format(row, field, fmt){
    var debug = false;
    
    var val = row[field.tag].val;
    if(val == null){ return ""; }
    var format = fmt.fmt;
    if(debug){ console.log("Format " + val + " via " + format); }
    var pct = false;
    var plus_minus = false; var plus_minus_sign = "";
    if(format.endsWith("%")){ pct = true; format = format.replace("%", ""); }
    if(format.startsWith("+/-")){ plus_minus = true; }
    var decimals = null;
    try{
        decimals = parseInt(format); 
    }
    catch(error){  }
    
    var res = null;
    if(["", "{}"].indexOf(format) > -1){
        res = val;
    }
    else if (typeof val == "string"){ res = val; }
    else if (decimals != null && ! pct){ res = val.toFixed(decimals); }
    else if (decimals == null && pct){ res = val*100.0  + "%"; }
    else if (decimals != null && pct){ res = (val*100.0).toFixed(decimals)  + "%"; }
    
    if(plus_minus){
        if(res == 0){ 
            res = "---";
        }
        else if (res > 0){ res = "+" + res; }
        else if (res < 0){ res = res; }
    }
    
    
    return res
}

var generic_specs = {};
function generic_create_table(td, specs=null){
    generic_td = td;
    console.log(td);

    var html = ""; var row_cnt = "";
    if(specs != null){ generic_specs = specs; }
    var target_elem = "#js_div";
    if( 'target_elem' in generic_specs ){ target_elem = generic_specs.target_elem; }
    if(target_elem.indexOf("#") != 0){ target_elem = "#"+target_elem; }
    var elem = $(target_elem); elem.empty();
    
    // START HEADER ROW
    var fields_printed = 0; var field = null;
    html += "<div class='col-12 no-padding flex'>";
    for(var a = 0;a<td.classes.length;a++){
        var cl = td.classes[a];
        cl.class += " no-padding";
        
        if('outer_class' in cl){
            cl.outer_class += " no-padding";
            html += "<div class='header maroon " + cl.outer_class + "'><ul class='table-ul' style='background-color:inherit;'>";
            for(var b = 0;b<cl.classes.length;b++){
                
                var sub_cl = cl.classes[b]; sub_cl.class += " no-padding";
                
                var onclick = "";
                field = td.fields[fields_printed];  fields_printed += 1; 
                if('sort_by' in field){ onclick = 'onclick="generic_sort_by_tag(\'' + field.sort_by + '\');"'; }
                html += "<li " + onclick + " style='' class='table-li "+sub_cl.class+"'><div class='large-cell-holder no-padding'>";
                if('display' in field){
                    html += "<span class='no-padding col-12 font-13'>" + field.display + "</span>";
                }
                else{
                    html += "<span class='no-padding col-12 font-13'><span class='no-padding dtop'>" + field.dtop_display + "</span><span class='no-padding mob'>" + field.mob_display + "</span></span>";
                }
                
                html += "</div></li>";
            }
            html += "</ul></div>";
        }
        else{
            var onclick = "";
            field = td.fields[fields_printed]; 
            //console.log(fields_printed);
            row_cnt = (fields_printed == 0 && !('no_row_count' in td)) ? "<div class='no-padding font-13'  style='width:25px;'>&nbsp;</div>" : ""; 
            //console.log(row_cnt);
            if('sort_by' in field){ onclick = 'onclick="generic_sort_by_tag(\'' + field.sort_by + '\');"'; }
            html += "<div " + onclick + " class='header maroon " + cl.class + ((fields_printed == 0) ? " flex" : "") + "'>";
            if('display' in field){
                html += row_cnt + "<span " + ((fields_printed==0) ?  "style='padding-left:5px;'" : "")+ " class='no-padding col-12 font-13'>" + field.display + "</span>";
            }
            else{
                html += row_cnt + "<span " + ((fields_printed==0) ?  "style='padding-left:5px;'" : "")+ " class='no-padding col-12 font-13'><span class='no-padding dtop'>" + field.dtop_display + "</span><span class='no-padding mob'>" + field.mob_display + "</span></span>";
            }
            html += "</div>";
            fields_printed += 1;
        }
    }
    html += "</div>";
    // DONE WITH HEADER ROW
    
    // START DATA ROWS
    for(var c = 0;c<td.data.length;c++){
        var row = td.data[c];
        
        var fields_printed = 0; var field = null;
        html += "<div class='table-row col-12 no-padding flex'>";
        for(var a = 0;a<td.classes.length;a++){
            var cl = td.classes[a];
            cl.class += " no-padding";
            
            if('outer_class' in cl){
                cl.outer_class += " no-padding";
                html += "<div class='" + cl.outer_class + "'><ul class='table-ul' style='background-color:inherit;'>";
                for(var b = 0;b<cl.classes.length;b++){
                    
                    var sub_cl = cl.classes[b]; sub_cl.class += " no-padding";
                    
                    field = td.fields[fields_printed];
                    fmt = td.fmt[fields_printed]; fields_printed += 1;
                    html += "<li style='' class='table-li "+sub_cl.class+"'><div class='large-cell-holder no-padding'>";

                    html += "<span " + ((fields_printed==0) ?  "style='padding-left:5px;'" : "")+ "  class='no-padding col-12 font-13'>" + generic_format(row, field, fmt) + "</span>";
                    html += "</div></li>";
                }
                html += "</ul></div>";
            }
            else{
                field = td.fields[fields_printed];
                fmt = td.fmt[fields_printed]; 
                row_cnt = (fields_printed == 0 && !('no_row_count' in td)) ? "<div class='no-padding font-13' style='width:25px; padding-left:5px;'>" + (c + 1) + "</div>" : ""; 
                html += "<div class='" + cl.class + ((fields_printed == 0) ? " flex" : "") + "'>";
                html += row_cnt + "<span " + ((fields_printed==0 && row_cnt == "") ?  "style='padding-left:5px;'" : "")+ "  class='no-padding col-12 font-13'>" + generic_format(row, field, fmt) + "</span>";
                html += "</div>";
                fields_printed += 1;
            }
        }
        html += "</div>";
    
    }
    // DONE WITH DATA ROWS
    elem.append(html);
    
}


// Live Win Probability Pages

function live_win_probabilities_switch_to_recap(go_forward=false){
    if(!go_forward){ return null; }
    $("#recap").removeClass("inactive").addClass("active")
    $("#plays").removeClass("active").addClass("inactive")
    $("#recap_button").removeClass("inactive").addClass("active")
    $("#plays_button").removeClass("active").addClass("inactive")
    $("#win_probability_row").addClass("hidden");
    $("#refresh_button_row").addClass("hidden");
}

function live_win_probabilities_switch_to_halftime(go_forward=false){
    if(!go_forward){ return null; }
    $("#recap").removeClass("inactive").addClass("active")
    $("#plays").removeClass("active").addClass("inactive")
    $("#recap_button").removeClass("inactive").addClass("active")
    $("#plays_button").removeClass("active").addClass("inactive")
    $("#win_probability_row").addClass("hidden");
    $("#refresh_button_row").addClass("hidden");
}

function expand_plays_past_thirty(){
    try{
        var steps = "4";
        document.getElementById("show_span").innerHTML = "1/" + steps;
        document.getElementById("show_span").innerHTML = "2/" + steps;
        document.getElementById("hidden_plays").style.display = "block";

        document.getElementById("show_span").innerHTML = "3/" + steps;
        document.getElementById("show_all_button_row").style.display = "none";
        document.getElementById("show_span").innerHTML = "4/" + steps;
    }
    catch(err){
        document.getElementById("show_span").innerHTML = err.message;
        
    }
}

function jump_to(go_to_label){ 
    __gaTracker('send', 'event', 'JumpTo', 'move', go_to_label.replace("_dtop", "").replace("_mob", "")); 
    location.href= ("#" + go_to_label); 
}

function auto_enable(src_page, label_str){
    label_str = label_str.toString();
    console.log("src_page: " + src_page + "\t\tlabel: " + label_str);
    console.log(label_str.includes("dtop"));
    if(src_page == "Bracketology" && label_str.includes("team") && label_str.includes("dtop")){
        console.log("Auto-jump to the " + "schedule_dtop" + " panel...");
        openCity("schedule_dtop");
    }
    else if(src_page == "Bracketology" && label_str.includes("team") && label_str.includes("mob")){
        console.log("Auto-jump to the " + "schedule_mob" + " panel...");
        openCity("schedule_mob");
    }
    else{
        openCity(label);
    }
    
}

function respond_to_survey(question, response){ 
    __gaTracker('send', 'event', 'SurveyResponse', question, response); 
}

function openCity(cityName) {
   
    __gaTracker('send', 'event', 'PanelContent', 'enable', cityName.replace("_dtop", "").replace("_mob", ""));
    var button_elem = document.getElementById(cityName + "_button");
   
    var i;
    var x = document.getElementsByClassName("zctab");
    for (i = 0; i < x.length; i++) {
        x[i].style.display = "none";
    }
  
    document.getElementById(cityName).style.display = "block";

    if(button_elem != null){
       if(button_elem.classList.contains("zc_toggle_button")){
            var borderStyle = null;
            x = document.getElementsByClassName("zc_toggle_button");
            for (i = 0; i < x.length; i++) {
                if (x[i].style.borderBottom != "none"){ borderStyle = x[i].style.borderBottom; }
                x[i].style.borderBottom = "none";
                x[i].style.fontWeight = 400;
            }
         
            button_elem.style.borderBottom = borderStyle; button_elem.style.fontWeight = 700;
        }
    } 
}
 

var team_stats_clicks = [];
function team_stats_set_offense(val){
    offense = val;
    team_stats_clicks.push("off" + val);
    if(val){ 
        $("#offense_tag").removeClass("tag-off").addClass("tag-on"); 
        $("#defense_tag").removeClass("tag-on").addClass("tag-off"); 
    }
    else{ 
        $("#defense_tag").removeClass("tag-off").addClass("tag-on"); 
        $("#offense_tag").removeClass("tag-on").addClass("tag-off");  
    }
    team_stats_display();
}

function team_stats_set_rate(val){
    stat_type = val;
    
    team_stats_clicks.push("rate" + val);
    $(".stat_type_tag").removeClass("tag-on").addClass("tag-off"); 
    $("#" + val + "_tag").removeClass("tag-off").addClass("tag-on"); 
    team_stats_display();
}


function team_stats_set_panel(val){
    panel = val;
    team_stats_clicks.push("panel" + val);
    $(".panel_tag").removeClass("tag-on").addClass("tag-off"); 
    $("#" + val + "_view_tag").removeClass("tag-off").addClass("tag-on"); 

    $(".panel").removeClass("visible").addClass("hidden"); 
    $("#" + val + "_view").removeClass("hidden").addClass("visible"); 

    if(team_stats_clicks.length != 0){ 
        var send_val = team_stats_clicks.join('|');
        __gaTracker('send', 'event', 'TeamStatsContent', 'enable', send_val);
    }
}

function team_stats_sort_by_tag(panel, tag){
    
    if(sort_tag[panel] == tag){
        sort_dir[panel] = ((sort_dir[panel] == "desc") ? "asc" : "desc");
    }
    else{
        sort_tag[panel] = tag;
        sort_dir[panel] = "desc";
        //if([""].indexOf(tag) > -1){ sort_dir[panel] = "asc"; }
    }
    team_stats_clicks.push("sort" + tag + sort_dir[panel]);
    
    var orig_sequence = [];
    for(var a = 0;a<misc.rows.length;a++){
        var row = misc.rows[a];
        
        if('data' in row && row.data != null){
            var val = null;
            
            for(var b = 0;b<row.data.length;b++){
                var cell = row.data[b];
                if(cell.tag == tag){ val = cell.val; break; }
            }
            var tup = {'seq': row.seq, 'ID': a, 'val': val};
            if(row.panel == panel && row.class == "data"){
                orig_sequence.push(tup);
            }
        }
    }
    //console.log(orig_sequence);
    var new_sequence = JSON.parse(JSON.stringify(orig_sequence));
    new_sequence.sort(function(first, second) {
        if(sort_dir[panel] == "desc"){
            return second.val - first.val;
        }
        else{
            return first.val - second.val;
        }
    });
    var cnt = new_sequence.length;
    var move_rows = [];
    //console.log(new_sequence);
    for(var a = 0;a<cnt;a++){
        move_rows.push(JSON.parse(JSON.stringify(misc.rows[new_sequence[a].seq])));
    }
    //console.log(move_rows);
    for(var a = 0;a<cnt;a++){
        var new_loc = orig_sequence[a].seq;
        misc.rows[new_loc] = (JSON.parse(JSON.stringify(move_rows[a])));
        misc.rows[new_loc].seq = new_loc;
    }
    //console.log("Sorted " + sort_dir[panel] + " by " + sort_tag[panel]);
    team_stats_display();
}


function team_stats_display(){
    //console.log(misc);
    
    var html = {'all_games': '', 'standard': '', 'by_opponents': ''}
    var printed = {};
    var elem = $("#stats_box"); elem.empty();
    
    if(team_stats_clicks.length != 0){ 
        var send_val = team_stats_clicks.join('|');
        __gaTracker('send', 'event', 'TeamStatsContent', 'enable', send_val);
    }
    
    for(var a = 0;a<misc.rows.length;a++){
        var row = misc.rows[a];
        //console.log(row);
        var display = false;
        if(offense && (row.offense == null || row.offense == 1)){ display = true; }
        else if(!offense && (row.offense == null || row.offense == 0)){ display = true; }
        
        if(display){
            if(row.class == "team-bg"){
                html[row.panel] += "<div class='" + row.class + " col-12 flex no-padding'>";
            }
            else{
                html[row.panel] += "<div class='table-row " + row.class + " col-12 flex no-padding'>";
            }
            if(row.data != null){
                html[row.panel] += "<div class='col-2-3 no-padding'><ul class='table-ul left' style='background-color:inherit;'>";
                for(var b = 0;b<1;b++){
                    var cell = row.data[b]; var txt = "";
                
                    var tmp = row.offense + row.panel;
                    //console.log(tmp)
                    if (!(tmp in printed)){ printed[tmp] = 1; }
                    
                    var txt = "<div  class='no-padding  " + cell.class + "'>";
                    
                    if(cell.class != 'header' && b == 0 && row.class == "data"){ txt += "<span style='padding-right:5px; ' class='font-12'>" + printed[tmp] + "</span>"; printed[tmp] += 1; }
                    else{ txt += "<span style='' class='font-12'></span>"; }
                    
                    if( 'dtop_str' in cell && cell.dtop_str != null){
                        txt += "<span style='' class='no-padding font-12 " + row.class + "'>";
                        txt += "<span style='' class='no-padding dtop'>"+ cell.dtop_str + "</span>";
                        txt += "<span style='' class='no-padding mob'>"+ cell.mob_str + "</span>";
                        txt += "</span>";
                    }
                    else{
                        txt += "<span style='' class='no-padding font-12 " + row.class + "'>" + cell.str + "</span>";
                    }
                    txt += "</div>";
                    
                    var onclick = "";
                    if('sort_by' in cell){ onclick = 'onclick="team_stats_sort_by_tag(\'' + row.panel + '\', \'' + cell.sort_by + '\');"'; }
                    html[row.panel] += "<li " + onclick + " style='' class='left'>" + txt + "</li>";
                    
                }
                html[row.panel] += "</ul></div>";
                html[row.panel] += "<div class='col-10-9 no-padding'><ul class='table-ul' style='background-color:inherit;'>";
                for(var b = 1; b<row.data.length;b++){
                    var cell = row.data[b];
                    var show_cell = false;
                    if(stat_type == "rate" && cell.stat_type == "rate"){ show_cell = true; }
                    else if(stat_type == "raw" && cell.stat_type == "raw"){ show_cell = true; }
                    else if(stat_type == "pace" && cell.stat_type == "pace"){ show_cell = true; }
                    else if(cell.stat_type == null){ show_cell = true; }
                    if(row.panel == "by_opponents" && cell.str == "Date"){ cell.str = ""; }
                    
                    var txt = "<div  class='no-padding cell-holder " + cell.class + "'>";
                    
                    if('mob_str' in cell && cell.mob_str != null){
                        txt += "<span style='' class='no-padding font-12 " + row.class + "'>";
                        txt += "<span class='no-padding dtop'>" + cell.dtop_str + "</span>";
                        txt += "<span class='no-padding mob'>" + cell.mob_str + "</span>";
                        txt += "</span>";
                    }
                    else{
                        txt += "<span style='' class='no-padding font-12 " + row.class + "'>" + cell.str + "</span>";
                    }
                    txt += "</div>";
                    if(show_cell){
                        var onclick = "";
                        if('sort_by' in cell){ onclick = 'onclick="team_stats_sort_by_tag(\'' + row.panel + '\', \'' + cell.sort_by + '\');"'; }
                        html[row.panel] += "<li " + onclick + " style='' class='center'>" + txt + "</li>";
                    }
                }
                html[row.panel] += "</ul></div>";
            }
            html[row.panel] += "</div>";
            
        }
    }
    
    
    html.standard = "<div id='standard_view' class='panel col-12" + ((panel == "standard") ? ' visible' : ' hidden') + "'>" + html.standard + "</div>";
    html.all_games = "<div id='all_games_view' class='panel col-12" + ((panel == "all_games") ? ' visible' : ' hidden') + "'>" + html.all_games + "</div>";
    html.by_opponents = "<div id='by_opponents_view' class='panel col-12" + ((panel == "by_opponents") ? ' visible' : ' hidden') + "'>" + html.by_opponents + "</div>";
    
    elem.append(html.standard);
    elem.append(html.all_games);
    elem.append(html.by_opponents);
}

// Live Win Probability Pages
var lwp_split_row = null;
var lwp_sequence = [];

function click_play_row(game_stream_ID, pct_elapsed, tag){
    if(lwp_split_row == null || lwp_split_row != pct_elapsed){
        //console.log("New pct: " + pct_elapsed);
        lwp_sequence = [];
        lwp_split_row = pct_elapsed;
    }
    lwp_sequence.push(tag);
    var seq = lwp_sequence.join("|");
    //console.log(seq);
    if(seq == "time|play|prob"){
        //console.log("Set the split at " + lwp_split_row + " for game stream " + game_stream_ID);
        document.getElementById('pixel').src = "https://lacrossereference.com/pixel?arg=" + game_stream_ID + "|" + lwp_split_row;
    }
}