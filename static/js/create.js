var offense = true;
var stat_type = "rate";
var panel = "standard";
var sort_by = null;


var sort_tag = {'generic': null, 'by_opponents': 'cnt', 'standard': 'date', 'all_games': 'date'};
var sort_dir = {'generic': 'desc', 'by_opponents': 'desc', 'standard': 'desc', 'all_games': 'desc'};


function respond_to_survey(question, response){ 
    __gaTracker('send', 'event', 'SurveyResponse', question, response); 
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