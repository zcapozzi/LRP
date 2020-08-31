

function copy_specs(src, target, overwrite){
    for(k in src){
        
        if(!(k in target) || overwrite){
            if( src[k] == null){ target[k] == null; }
            else if(["string", "number", "boolean"].indexOf(typeof src[k]) > -1){ target[k] = src[k]; }
            else if( !(src[k] instanceof Array)){ // It's a dict
                target[k] = copy_specs(src[k], target[k], overwrite)
            }
            else if( (src[k] instanceof Array)){ // It's an array
                target[k] = [];
                for(var a = 0;a<src[k].length;a++){
                    target[k].push(src[k][a]);
                }
            }
            else{
                console.log("Uncaught type: " + (typeof src[k]));
            }
        }
    }
    return target;
}

function get_client_width(elem_name){
    var client_width = $("#" + elem_name).width();//document.getElementById(elem_name).clientWidth;
    //console.log("Element: " + elem_name); console.log("Client width: " + client_width);
    return client_width;
}
function get_client_height(elem_name){
    var client_height = $("#" + elem_name).height();//document.getElementById(elem_name).clientWidth;
    //console.log("Element: " + elem_name); console.log("Client height: " + client_height);
    return client_height;
}

function finish_specs(specs){
    // Set all the default specifications if they were not included in the actual object
    defaults = []
    // tag: val
    defaults.push({'tag': 'margin_top', 'val': 60});
    defaults.push({'tag': 'margin_right', 'val': 10});
    defaults.push({'tag': 'margin_left', 'val': 30});
    defaults.push({'tag': 'margin_bottom', 'val': 40});
    defaults.push({'tag': 'chart_size', 'val': "normal"});
    defaults.push({'tag': 'shading_vars', 'val': null});
    defaults.push({'tag': 'flip', 'val': false});
    
    
    for(var a = 0;a<defaults.length;a++){
        d = defaults[a];
        if(!(d['tag'] in specs)){
            specs[d['tag']] = d['val'];
        }
    }
    return specs
}

function initiate_svg(id, specs, initial_specs){
    
    time_log.push({'tag': "Finish Specs", 'start': new Date().getTime()});
    specs = finish_specs(specs)
    time_log[time_log.length-1].end = new Date().getTime();
    
    time_log.push({'tag': "Finished Initial Copy", 'start': new Date().getTime()});
    /* Set up the specs, including any transitions */
    if(initial_specs == null){
        specs.transition = false;
        initial_specs = JSON.parse(JSON.stringify(specs));
    }
    else{
        specs.transition = true;
        initial_specs = copy_specs(specs, initial_specs, false);
    }
    
    time_log[time_log.length-1].end = new Date().getTime();
    
    /* Create graph */
    
    var client_width = get_client_width(id);
    var client_height = get_client_height(id);
    
    
    
    var width = client_width - initial_specs.margin_left - initial_specs.margin_right,
                height = client_height - initial_specs.margin_top - initial_specs.margin_bottom;
                
    
    
    
    d3.select("#" + id).selectAll("*").remove();          
    var svg = d3.select("#" + id).append("svg")
                .attr("width", width + initial_specs.margin_left + initial_specs.margin_right)
                .attr("height", height + initial_specs.margin_top + initial_specs.margin_bottom)
                .append("g")
                .attr("transform", "translate(" + initial_specs.margin_left + "," + initial_specs.margin_top + ")");
    
    return {width, height, specs, initial_specs, svg};
}
function horizontal_line(data, id, arg_specs, arg_initial_specs = null){
    var debug = {'on': true, 'spacing': true, 'data': true};
    time_log.push({'tag': "Initiate SVG", 'start': new Date().getTime()});
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, arg_specs, arg_initial_specs);
    time_log[time_log.length-1].end = new Date().getTime();
    
    if(debug.on && debug.spacing){
        console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height));
    }
    
    /* Create graph */
    
    var x = d3.scaleLinear().range([0, width]);
    var y = d3.scaleLinear().range([height, 0]);
    if(debug.on && debug.data){
        console.log(data);
    }
    
    
    
    var min_x_val = null;
    var min_y_val = null;
    var max_x_val = null;
    var max_y_val = null;
    
    if('max_x' in data){
        min_x_val = data.min_x;
        max_x_val = data.max_x;
    }
    else{
        for(var a = 0;a<data.data.length;a++){    
            var tmp_data = data.data[a];
            if(min_x_val == null || min_x_val > d3.min(tmp_data.points, function(d) { return d.x; })){
                min_x_val = d3.min(tmp_data.points, function(d) { return d.x; });
            }
            if(max_x_val == null || max_x_val < d3.max(tmp_data.points, function(d) { return d.x; })){
                max_x_val = d3.max(tmp_data.points, function(d) { return d.x; });
            }
            
        }
    }
    if('max_y' in data){
        min_y_val = data.min_y;
        max_y_val = data.max_y;
    }
    else{
        for(var a = 0;a<data.data.length;a++){ 
            var tmp_data = data.data[a];
            if(min_y_val == null || min_y_val > d3.min(tmp_data.points, function(d) { return d.y; })){
                min_y_val = d3.min(tmp_data.points, function(d) { return d.y; });
            }
            if(max_y_val == null || max_y_val < d3.max(tmp_data.points, function(d) { return d.y; })){
                max_y_val = d3.max(tmp_data.points, function(d) { return d.y; });
            }
            
        }
    }
    
    
    x.domain([min_x_val, max_x_val]);
    if(initial_specs.flip){
        y.domain([max_y_val, min_y_val]);
    }
    else{
        y.domain([min_y_val, max_y_val]);
    }
    // Handle the X-Axis
    
    
    if('x_ticks' in data){
        svg.append("line")
            .attr("x1", x(min_x_val)).attr("y1", height)
            .attr("x2", x(max_x_val)).attr("y2", height)
            .style("stroke-width", 1.5).style("stroke", "rgb(213, 213, 213)").style("fill", "none");
        
        for(var a = 0;a<data.x_ticks.length;a++){
            var tick = data.x_ticks[a];
    
            svg.append("text")
                .attr("x", x(tick.x)).attr("y", height + 15)
                .attr("text-anchor", function (d) { return "middle";  }  )
                .attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                //style('font-size', '10px').style('font-family', 'Arial')
                .text(tick.label);
                
        }
    }
    
    // Handle the Y-Axis
    if('y_ticks' in data){
        svg.append("line")
            .attr("x1", x(min_x_val)).attr("y1", y(min_y_val))
            .attr("x2", x(min_x_val)).attr("y2", y(max_y_val))
            .style("stroke-width", 1.5).style("stroke", "rgb(213, 213, 213)").style("fill", "none");
            
        for(var a = 0;a<data.y_ticks.length;a++){
            var tick = data.y_ticks[a];
            svg.append("text")
                .attr("y", y(tick.y) + 3).attr("x", x(min_x_val) - 5)
                .attr("text-anchor", function (d) { return "end";  }  )
                .attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                //.style("fill", "#555").style('font-size', '11px').style('font-family', 'Arial')
                .text(tick.label);
            
            svg.append("line")
            .attr("x1", x(min_x_val)).attr("y1", y(tick.y))
            .attr("x2", x(max_x_val)).attr("y2", y(tick.y))
            .style("stroke-width", 1).style("stroke", "rgb(233, 233, 233)").style("fill", "none");
        
        }
    }
    
    tmp = svg.append("text")
        .attr("text-anchor", function (d) { return "middle";  }  )
        .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
        //.style("fill", "#555").style('font-size', '14px').style('font-family', 'Arial')
        .attr("transform", "rotate(-90)")
        .attr("y", 0).attr("dy", -initial_specs.margin_left+20)
        .attr("x", 0).attr("dx", -y((min_y_val + max_y_val)/2))
        .text(data.axis_labels.y)
        ;
        

       
    tmp = svg.append("text")
        .attr("x", x((min_x_val + max_x_val)/2)).attr("y", height + 34)
        .attr("text-anchor", function (d) { return "middle";  }  )
        .attr("class", 'lightish chart-axis-label ' + initial_specs.chart_size)
        //.style("fill", "#555").style('font-size', '14px').style('font-family', 'Arial')
        .text(data.axis_labels.x);
    
    icon_offset = -15;
    if('detail_url' in data && data.detail_url != null){
        svg.append("svg:image").attr("xlink:href", "static/img/popout15.png")
                .attr("x", x(max_x_val)+icon_offset).attr("y", -initial_specs.margin_top + 5).attr("width", "15")
                .attr("height", "15").attr("onclick", "window.location='" + data.detail_url + "';");
        icon_offset -= 20;
    }
    
    if('explanation' in data && data.explanation != null){
        if(data.explanation.indexOf("|") > -1){
            svg.append("svg:image").attr("xlink:href", "static/img/Gray_Info15.png")
                .attr("x", x(max_x_val)+icon_offset).attr("y", -initial_specs.margin_top + 5).attr("width", "15")
                .attr("height", "15").attr("onclick", "show_explanation('');");
            icon_offset -= 20;
        }
        else{
            console.log("ERROR: Explanation format is bad\n\n" + data.explanation);
        }
    }


    if('title' in data){
        svg.append("text")
        .attr("x", -initial_specs.margin_left).attr("y", -initial_specs.margin_top + 20)
        .attr("text-anchor", function (d) { return "start";  }  )
        .attr("class", "lightish chart-title-label " + initial_specs.chart_size)
        .text(data.title);    
    }
    
    var line = d3.line()
        .curve(d3.curveLinear)
        .x(function(d){ return x(d.x); })
        .y(function(d){ return y(d.y); });

    for(var a = 0;a<data.data.length;a++){
        tmp_data = data.data[a];
        svg.append("path")
          .datum(tmp_data.points)
          .attr("fill", "none")
          .attr("stroke", tmp_data['stroke'])
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round")
          .attr("stroke-dasharray", tmp_data['stroke-dasharray'])
          .attr("stroke-width", 2)
          .attr("d", line);
    }
}

function create_pct_y_ticks(points){
    var res = {'ticks': [], 'max': null, 'min':  null};
    max_eff = null; min_eff = null;
    for(var a = 0;a<points.length;a++){
        var g = points[a];
        if(max_eff == null || max_eff < g.y){ max_eff = g.y; }
        if(min_eff == null || min_eff > g.y){ min_eff = g.y; }
    }
    
    alt_min_eff = min_eff - .1;
    alt_max_eff = max_eff + .1;
    //console.log("Alt Eff Range: " + alt_min_eff + " - " + alt_max_eff);
    
    rounded_min_eff = Math.round(alt_min_eff * 100.0 / 10)/10;
    rounded_max_eff = Math.round(alt_max_eff * 100.0 / 10)/10;
    //console.log("Rounded Eff Range: " + rounded_min_eff + " - " + rounded_max_eff);
    diff = rounded_max_eff - rounded_min_eff;
    var num_ticks = 5;
    
    if(Math.abs(diff -.1) < .001){ num_ticks = 5; }
    else if(Math.abs(diff -.2) < .001){ num_ticks = 5; }
    else if(Math.abs(diff -.3) < .001){ num_ticks = 4; }
    else if(Math.abs(diff -.4) < .001){ num_ticks = 5; }
    else if(Math.abs(diff -.5) < .001){ num_ticks = 6; }
    else if(Math.abs(diff -.6) < .001){ num_ticks = 4; }
    else if(Math.abs(diff -.7) < .001){ num_ticks = 8; }
    else if(Math.abs(diff -.8) < .001){ num_ticks = 5; }
    else if(Math.abs(diff -.9) < .001){ num_ticks = 4; }
    else if(Math.abs(diff -1.0) < .001){ num_ticks = 6; }
    
    inc = (diff) / (num_ticks-1);
    //console.log("Diff: " + diff + "   Inc: " + inc);
    
    for(var a = 0;a<num_ticks;a++){
        
        //var tmp_y = rounded_min_eff + inc*a;
        var tmp = rounded_min_eff + inc*a;
        res.ticks.push({'y': rounded_min_eff + inc*a, 'label': Math.round(100.0 * (rounded_min_eff + inc*a)) + "%"});
        if(res.min == null || res.min > tmp){ res.min = tmp; }
        if(res.max == null || res.max < tmp){ res.max = tmp; }
    }
    //console.log("res");
    //console.log(res);
    return res;
}

function create_numeric_y_ticks(points){
    var res = {'ticks': [], 'max': null, 'min':  null};
    max_eff = null; min_eff = null;
    for(var a = 0;a<points.length;a++){
        var g = points[a];
        if(max_eff == null || max_eff < g.y){ max_eff = g.y; }
        if(min_eff == null || min_eff > g.y){ min_eff = g.y; }
    }
    
    inc = (max_eff - min_eff) * .05;
    alt_min_eff = min_eff - inc;
    alt_max_eff = max_eff + inc;
    console.log("Alt Eff Range: " + alt_min_eff + " - " + alt_max_eff);
    
    rounded_min_eff = Math.round(alt_min_eff);
    rounded_max_eff = Math.round(alt_max_eff);
    console.log("Rounded Eff Range: " + rounded_min_eff + " - " + rounded_max_eff);
    diff = rounded_max_eff - rounded_min_eff;
    var num_ticks = 5;
    
    if(diff < 10){ num_ticks = 5; }
    else if(diff < 20){ num_ticks = 5; }
    else if(diff < 30){ num_ticks = 4; }
    else if(diff < 40){ num_ticks = 5; }
    else if(diff < 50){ num_ticks = 6; }
    else if(diff < 60){ num_ticks = 4; }
    else if(diff < 70){ num_ticks = 8; }
    else if(diff < 80){ num_ticks = 5; }
    else if(diff < 90){ num_ticks = 4; }
    else if(diff < 100){ num_ticks = 6; }
    
    inc = (diff) / (num_ticks-1);
    //console.log("Diff: " + diff + "   Inc: " + inc);
    
    for(var a = 0;a<num_ticks;a++){
        
        //var tmp_y = rounded_min_eff + inc*a;
        var tmp = rounded_min_eff + inc*a;
        res.ticks.push({'y': rounded_min_eff + inc*a, 'label': Math.round( (rounded_min_eff + inc*a))});
        if(res.min == null || res.min > tmp){ res.min = tmp; }
        if(res.max == null || res.max < tmp){ res.max = tmp; }
    }
    //console.log("res");
    //console.log(res);
    return res;
}

function create_game_x_ticks(points){
    var res = {'ticks': [], 'max': null, 'min':  null};
    
    if(points.length > 8){
        for(var a = 0;a<points.length;a++){ var g = points[a];
            res.ticks.push({'x': g.x, 'label': (('seq' in g) ? g.seq : '')});
        }
        //data['x_ticks'] = [{'x': 1, 'label': "G1"}, {'x': 2, 'label': "G2"}, {'x': 3, 'label': "G3"}, {'x': 4, 'label': "G4"}]
    }
    else if(points.length > 6){
        for(var a = 0;a<points.length;a++){ var g = points[a];
            res.ticks.push({'x': g.x, 'label': g.seq});
        }
        
    }
    else if(points.length > 2){
        for(var a = 0;a<points.length;a++){ var g = points[a];
            res.ticks.push({'x': g.x, 'label': g.dt});
        }
        
    }
    else{
        for(var a = 0;a<points.length;a++){ var g = points[a];
            res.ticks.push({'x': g.x, 'label': g.dt});
        }
    }
    
    for(var a = 0;a<res.ticks.length;a++){
        var tick = res.ticks[a];
        if(res.min == null || res.min > tick.x){ res.min = tick.x; }
        if(res.max == null || res.max < tick.x){ res.max = tick.x; }
    }
    
    if(res.ticks.length == 2){
        diff = res.max-res.min; diff_inc = diff * .1;
        res.min -= diff_inc;
        res.max += diff_inc;
    }
    else if(res.ticks.length > 2){
        diff = res.max-res.min; diff_inc = diff * .025;
        res.min -= diff_inc;
        res.max += diff_inc;
    }
    
    return res;
}

function custom_last_game_tile(misc, id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': false};
    time_log.push({'tag': "Initiate SVG", 'start': new Date().getTime()});
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, arg_specs, arg_initial_specs);
    time_log[time_log.length-1].end = new Date().getTime();
    
    var tags = [];
    tags.push({'label': 'Offense', 'var': 'off_efficiency_exclusive', 'league_var': 'off_efficiency'});
    tags.push({'label': 'Defense', 'var': 'def_efficiency_inverted_exclusive', 'league_var': 'def_efficiency_inverted'});
    tags.push({'label': 'Faceoffs', 'var': 'faceoff_win_rate_exclusive', 'league_var': 'faceoff_win_rate'});
    
    
    for(var a=0;a<tags.length;a++){
        var tag = tags[a];
        tag.height = 50 * a + 30;
        tag.game = misc.data.last_game[tag.league_var];
        tag.my_avg = misc.data[tag.var];
        tag.league_avg = misc.data["league_" + tag.league_var];
        tag.league_low = misc.data["10_90_range_" + tag.league_var][0];
        tag.league_high = misc.data["10_90_range_" + tag.league_var][1];
        
        tag.rng = tag.league_high - tag.league_low;
        tag.ranges = []
        tag.inc = tag.rng * .01;
        for(var b = 0;b<1000;b++){
            tag.ranges.push({'extension': b, 'high': misc.data["10_90_range_" + tag.league_var][1] + tag.inc*b, 'low': misc.data["10_90_range_" + tag.league_var][0] - tag.inc*b})
            
            
        }
        
        tag.game_relative = tag.game-tag.league_low;
        tag.my_avg_relative = tag.my_avg-tag.league_low;
        tag.game_relative_to_range_as_pct = tag.game_relative/tag.rng;
        tag.my_avg_relative_to_range_as_pct = tag.my_avg_relative/tag.rng;
        tag.cutoff = null;
        for(var b = 0;b<tag.ranges.length;b++){
            rng = tag.ranges[b]; rng.diff = rng.high - rng.low;
            game_relative = tag.game-rng.low;
            my_avg_relative = tag.my_avg-rng.low;
            game_relative_to_range_as_pct = game_relative/rng.diff;
            my_avg_relative_to_range_as_pct = my_avg_relative/rng.diff;
            if(game_relative_to_range_as_pct >= 0 && game_relative_to_range_as_pct <= 1 && my_avg_relative_to_range_as_pct >= 0 && my_avg_relative_to_range_as_pct <= 1){
                if(tag.cutoff == null){ tag.cutoff = b; }
                rng.success = 1;
            }
            else{
                rng.success = 0;
            }
        }
    
    }
    
    for(var a = 0;a<tags.length;a++){
        var tag = tags[a];
        rng = tag.ranges[tag.cutoff]; rng.diff = rng.high - rng.low;
        tag.game_relative = tag.game-rng.low;
        tag.my_avg_relative = tag.my_avg-rng.low;
        tag.game_relative_to_range_as_pct = tag.game_relative/rng.diff;
        tag.my_avg_relative_to_range_as_pct = tag.my_avg_relative/rng.diff;
            
    }
    
    var max_cutoff = null;
    for(var a= 0;a<tags.length;a++){
        if(tags[a].cutoff != null && (max_cutoff == null || max_cutoff < tags[a].cutoff)){
            max_cutoff = tags[a].cutoff;
        }
    }
    
    var x = d3.scaleLinear().range([0, width]);
    var y = d3.scaleLinear().range([height, 0]);
    x.domain([0, 1]);
    y.domain([0, height]);
    
    svg.append("line")
            .attr("x1", x(.60)).attr("y1", 35)
            .attr("x2", x(.60)).attr("y2", height-35)
            .style("stroke-width", 1.5).style("stroke", "rgb(173, 173, 173)").style("fill", "none").style('stroke-dasharray', '2,2');
    
    svg.append("text")
            .attr("x", x(.60)).attr("y", height-20)
            .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
            .attr("text-anchor", function (d) { return "middle";  }  )
            .text("Median Team");
    
    // Legend
    svg.append("line")
        .attr("x1", x(.03)).attr("y1", height - 26)
        .attr("x2", x(.08)).attr("y2", height - 26)
        .style("stroke-width", 2.5).style("stroke", "#F00").style("fill", "none").style('stroke-dasharray', '3,3');

    svg.append("text")
            .attr("x", x(.10)).attr("y", height - 23)
            .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
            .attr("text-anchor", function (d) { return "start";  }  )
            .text("vs " + misc.data.last_game.opp_short_code);
        
    svg.append("line")
        .attr("x1", x(.03)).attr("y1", height - 11)
        .attr("x2", x(.08)).attr("y2", height - 11)
        .style("stroke-width", 2.5).style("stroke", "#00F").style("fill", "none").style('stroke-dasharray', '3,3');

    svg.append("text")
            .attr("x", x(.10)).attr("y", height - 8)
            .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
            .attr("text-anchor", function (d) { return "start";  }  )
            .text("Season Avg.");
            
            
    
    
    for(var a= 0;a<tags.length;a++){
        var tag = tags[a];
    
        svg.append("text")
            .attr("x", 0).attr("y", tag.height)
            .attr("text-anchor", function (d) { return "start";  }  )
            .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
            .text(tag.label);  
        /*svg.append("text")
            .attr("x", width).attr("y", tag.height)
            .attr("text-anchor", function (d) { return "end";  }  )
            .attr("class", "light chart-tick-label " + initial_specs.chart_size)
            .text(Math.round(100*tag.game) + "% / " + Math.round(100*tag.my_avg) + "% / (" + Math.round(100*tag.league_low) + "%" +  + Math.round(100*tag.league_avg) + "%" +  + Math.round(100*tag.league_high) + "%" + ")");  
        */
        // Print the default rect
        svg.append("rect")
            .attr("x", x(.30))
            .attr("y", tag.height + 15)
            .attr("width", x(.6))
            .attr("height", 10)
            .style("fill", "#FFF")
            .style('stroke', '#888');
        
        // Print the game result
        svg.append("line")
            .attr("x1", x(tag.game_relative_to_range_as_pct*.6 + .30)).attr("y1", tag.height + 00)
            .attr("x2", x(tag.game_relative_to_range_as_pct*.6 + .30)).attr("y2", tag.height + 40)
            .style("stroke-width", 1.5).style("stroke", "#F00").style("fill", "none").style('stroke-dasharray', '3,3');
    
        // Print your average result
        svg.append("line")
            .attr("x1", x(tag.my_avg_relative_to_range_as_pct*.6 + .30)).attr("y1", tag.height + 10)
            .attr("x2", x(tag.my_avg_relative_to_range_as_pct*.6 + .30)).attr("y2", tag.height + 30)
            .style("stroke-width", 1.5).style("stroke", "#00F").style("fill", "none").style('stroke-dasharray', '1,1');
    
        
        
    }
    if(debug.on && debug.spacing){
        console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height));
    }
    
    data = misc.data;
}

function custom_next_game_tile(misc, id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': false};
    time_log.push({'tag': "Initiate SVG", 'start': new Date().getTime()});
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, arg_specs, arg_initial_specs);
    time_log[time_log.length-1].end = new Date().getTime();
    
    var tags = [];
    tags.push({'label': 'Off', 'var': 'off_efficiency'});
    tags.push({'label': 'Def', 'var': 'def_efficiency_inverted'});
    tags.push({'label': 'FO%', 'var': 'faceoff_win_rate'});
    
    var num_games = misc.data.next_game.history.length;
    for(var a = 0;a<num_games;a++){
        var game = misc.data.next_game.history[a];
        game.show = 1;
        game.bottom_indicator = 0;
        if(specs.version == "aggregate"){
            if(a < 2 || a > num_games - 3){
                game.show = 1;
            }
            else{
                game.show = 0;
            }
            if(a == 2){
                game.bottom_indicator = 1;
            }
        }
        
        
        game.top_indicator = null;
        
        if(specs.version == "aggregate"){
            if(a == 0){ game.top_indicator = "2 Best Games"; }
            if(a == num_games - 2){ game.top_indicator = "2 Worst Games"; }
        }
    }
    
    var elem = $("#" + id); elem.empty();
    var header = "";
    header += "<div id='next_game_header_row' class='bbottom flex no-padding' style='margin-top:10px; margin-bottom: 3px;'>";
    header += "<div class='col-3'><span class='font-14 bold'>Opp.</span></div>"
    for(var b = 0;b<tags.length;b++){
        var tag = tags[b];
        header += "<div class='col-3 centered'><span class='font-14 bold'>" + tag.label + "</span></div>"
    }
    header += "</div>"
    
    elem.append(header);
    
    var which = "top";
    for(var a = 0;a<misc.data.next_game.history.length;a++){
        var game = misc.data.next_game.history[a];
        if(game.show){
            //console.log(game);
        
            if(which == "top" && game.top_indicator != null){
                html = "";
                html += "<div class='no-padding'>";
                html += "<div class='col-12 no-padding'><span class='font-12' style='font-style:italic;'>" + game.top_indicator + "</span></div>"
                html += "</div>"
                elem.append(html);
            }
            
            html = "";
            html += "<div class='flex opp-game-row' style='padding:4px;'>";
            html += "<div class='col-3 no-padding'><span class='font-14'>" + game.opp_short_code + "</span></div>"
            for(var b = 0;b<tags.length;b++){
                var tag = tags[b];
                html += "<div class='col-3 no-padding centered'><span class='large-dot' style='background-color: " + game['color_' + tag.var] + ";'>" + "</span></div>";
            
            }
            html += "</div>"
            elem.append(html);
        }
    }
    
    if(misc.data.next_game.history.length == 4){
        html = "";
        html += "<div class='flex opp-game-row' style='padding:4px;'>";
        html += "<div class='col-3 no-padding'><span class='font-14'></span></div>"
        for(var b = 0;b<tags.length;b++){
            var tag = tags[b];
            html += "<div class='col-3 no-padding centered'></div>";
        
        }
        html += "</div>"
        elem.append(html);
    }
}


function rnd(a){ return Math.round(a); }