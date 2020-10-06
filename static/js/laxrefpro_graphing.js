

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
    defaults.push({'tag': 'margin_top', 'val': 5});
    defaults.push({'tag': 'highlight_team', 'val': 0});
    defaults.push({'tag': 'highlight_color', 'val': "orange"});
    defaults.push({'tag': 'margin_right', 'val': 10});
    defaults.push({'tag': 'margin_left', 'val': 30});
    defaults.push({'tag': 'margin_bottom', 'val': 40});
    defaults.push({'tag': 'chart_size', 'val': "normal"});
    defaults.push({'tag': 'shading_vars', 'val': null});
    defaults.push({'tag': 'vertical_lines', 'val': []});
    defaults.push({'tag': 'flip', 'val': false});
    defaults.push({'tag': 'fill', 'val': '#88F'});
    
    for(var a = 0;a<defaults.length;a++){
        d = defaults[a];
        if(!(d['tag'] in specs)){
            specs[d['tag']] = d['val'];
        }
    }
   
    return specs
}

function initiate_svg(id, data, specs, initial_specs){
    
    //time_log.push({'tag': "Finish Specs", 'start': new Date().getTime()});
    specs = finish_specs(specs)
    //time_log[time_log.length-1].end = new Date().getTime();
    
    //time_log.push({'tag': "Finished Initial Copy", 'start': new Date().getTime()});
    /* Set up the specs, including any transitions */
    if([null, {}].indexOf(initial_specs) > -1){
        specs.transition = false;
        initial_specs = JSON.parse(JSON.stringify(specs));
    }
    else{
        specs.transition = true;
        initial_specs = copy_specs(specs, initial_specs, false);
    }
    
    initial_specs.final_margin_top = initial_specs.margin_top;
    specs.final_margin_top = specs.margin_top;
    if(data != null && typeof data.axis_labels != "undefined"){
        if([null, ''].indexOf(data.axis_labels.y) == -1){
            initial_specs.final_margin_top = initial_specs.margin_top + 25;
            specs.final_margin_top = specs.margin_top + 25;
            
        }
    }
    
    
    //time_log[time_log.length-1].end = new Date().getTime();
    
    /* Create graph */
    
    var client_width = get_client_width(id);
    var client_height = get_client_height(id);
    
    if('width' in initial_specs){ client_width = initial_specs.width; }
    if('height' in initial_specs){ client_height = initial_specs.height; }
    
    
    
    var width = client_width - initial_specs.margin_left - initial_specs.margin_right,
                height = client_height - initial_specs.final_margin_top - initial_specs.margin_bottom;
    
    if(client_height > 50 && initial_specs.chart_type != "spark"){ height -= 5; }
    
    //console.log("ID: " + id + "  SVG Width: " + width + "  SVG Height: " + height);
    //console.log(client_height, initial_specs.final_margin_top, initial_specs.margin_bottom, initial_specs.final_margin_left, initial_specs.margin_right);
    var svg = null;

    if(width >= 0){
    
    
        d3.select("#" + id).selectAll("*").remove();  
        
        
        svg = d3.select("#" + id).append("svg")
                    .attr("width", width + initial_specs.margin_left + initial_specs.margin_right)
                    .attr("height", height + initial_specs.final_margin_top + initial_specs.margin_bottom)
                    .append("g")
                    .attr("transform", "translate(" + initial_specs.margin_left + "," + initial_specs.final_margin_top + ")");
    }
    
    return {width, height, specs, initial_specs, svg};
}

function graph_print_x_axis(svg, x, data, width, height, min_x_val, max_x_val, chart, initial_specs){
    
    if('x_ticks' in data){
        svg.append("line")
            .attr("x1", x(min_x_val)).attr("y1", height)
            .attr("x2", width).attr("y2", height)
            .style("stroke-width", 1.5).style("stroke", "rgb(213, 213, 213)").style("fill", "none");
        
        for(var a = 0;a<data.x_ticks.length;a++){
            var tick = data.x_ticks[a];
            
            function tick_placement(x, loc, chart){
                if(['vertical_bars'].indexOf(chart.type) > -1){
                    return chart.bandwidth_offset + chart.bandwidth/2 + x(loc);
                }
                else{
                    return x(loc);
                }
            }
            
            svg.append("text")
                .attr("x", tick_placement(x, tick.x, chart)).attr("y", height + 15)
                .attr("text-anchor", function (d) { return "middle";  }  )
                .attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                //style('font-size', '10px').style('font-family', 'Arial')
                .text(tick.label);
                
        }
    }
    
    
    svg.append("text")
        .attr("x", (width - x(min_x_val))/2).attr("y", height + 34)
        .attr("text-anchor", function (d) { return "middle";  }  )
        .attr("class", 'lightish chart-axis-label ' + initial_specs.chart_size)
        //.style("fill", "#555").style('font-size', '14px').style('font-family', 'Arial')
        .text(data.axis_labels.x);
    return svg;
}
    
function graph_add_shading_ranges(svg, data, x, y, initial_specs){

    low_v = initial_specs.shading_vars[0];
    high_v = initial_specs.shading_vars[1];
    
    for(var a = 0;a<data.data.length;a++){
        tmp_data = data.data[a];
    
        for(var a = 0;a<tmp_data.points.length;a++){
            var g = tmp_data.points[a];
            
            rect_height = y(g[high_v]) - y(g[low_v])
            svg.append("rect")
                .attr("x", Math.max(1, x(g.x) - initial_specs.shading_vars_rect_width)).attr("y", y(g[low_v]))
                .attr("width", initial_specs.shading_vars_rect_width).attr("height", rect_height)
                .style("fill", "#FEE");
        }
        
    }

    return svg;
}
    
function graph_add_shading_legend(svg, x, data, height, min_x_val, max_x_val, initial_specs){
    svg.append("rect")
        .attr("x", -initial_specs.margin_left + 5)
        .attr("y", height + initial_specs.margin_bottom - 18)
        .attr("width", 15).attr("height", 8)
        .style("fill", "#FDD")
        ;
    svg.append("text")
        .attr("x", -initial_specs.margin_left + 25).attr("y",  height + initial_specs.margin_bottom - 10)
        .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
        .attr("text-anchor", function (d) { return "start";  }  )
        .text("90% of outcomes");return svg;
}
    
function graph_print_y_axis(svg, x, y, data, width, height, min_x_val, max_x_val, min_y_val, max_y_val, initial_specs){
    if('y_ticks' in data){
        svg.append("line")
            .attr("x1", x(min_x_val)).attr("y1", y(min_y_val))
            .attr("x2", x(min_x_val)).attr("y2", y(max_y_val))
            .style("stroke-width", 1.5).style("stroke", "rgb(213, 213, 213)").style("fill", "none");
        
        for(var a = 0;a<data.y_ticks.length;a++){
            var tick = data.y_ticks[a];
            
            if(tick.y >= min_y_val){
                svg.append("text")
                    .attr("y", y(tick.y) + 3).attr("x", x(min_x_val) - 5)
                    .attr("text-anchor", function (d) { return "end";  }  )
                    .attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                    //.style("fill", "#555").style('font-size', '11px').style('font-family', 'Arial')
                    .text(tick.label);
                
                svg.append("line")
                .attr("x1", x(min_x_val)).attr("y1", y(tick.y))
                .attr("x2", width).attr("y2", y(tick.y))
                .style("stroke-width", 1).style("stroke", "rgb(233, 233, 233)").style("fill", "none");
            }
        
        }
    }
    
    if(rotated = false){
        svg.append("text")
            .attr("text-anchor", function (d) { return "middle";  }  )
            .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
            .attr("transform", "rotate(-90)").attr("letter-spacing", 1)
            .attr("y", 0).attr("dy", -initial_specs.margin_left+20)
            .attr("x", 0).attr("dx", -y((min_y_val + max_y_val)/2))
            .text(data.axis_labels.y);
    }
    else{
        
        svg.append("text")
            .attr("text-anchor", function (d) { return "start";  }  )
            .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
            .attr("y", -initial_specs.final_margin_top + 15)
            .attr("x", -initial_specs.margin_left + 0)
            .text(data.axis_labels.y);
    }
    return svg;
}

function print_y_label(svg, data, initial_specs){
    svg.append("text")
            .attr("text-anchor", function (d) { return "start";  }  )
            .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
            .attr("y", -initial_specs.final_margin_top + 15)
            .attr("x", -initial_specs.margin_left + 0)
            .text(data.axis_labels.y);
    return svg;
}

function graph_print_vertical_lines(svg, x, height, initial_specs){
    if(!('vertical_lines' in initial_specs) || initial_specs.vertical_lines == null){ return svg; }
    for(var a = 0;a<initial_specs.vertical_lines.length;a++){
        var l = initial_specs.vertical_lines[a];
        
        svg.append("line")
            .attr("x1", x(l.x)).attr("y1", 0)
            .attr("x2", x(l.x)).attr("y2", height)
            .style("stroke-width", 1).style("stroke-dasharray", "2,2").style("stroke", "rgb(213, 213, 213)").style("fill", "none");
            
        if('label' in l){
            svg.append("text")
                .attr("x", function(d){ if(l.align == "end"){ return x(l.x) - 5;} else {return x(l.x) + 5;}})
                .attr("y", 10)
                .attr("text-anchor", function (d) { return l.align;  }  )
                .attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                //style('font-size', '10px').style('font-family', 'Arial')
                .style('font-style', 'italic')
                .text(l.label);
        }
    }
    return svg;
}

function graph_add_link_icon(icon_offset, svg, data, initial_specs){
    svg.append("svg:image").attr("xlink:href", "static/img/popout15.png")
        .attr("x", x(max_x_val)+icon_offset).attr("y", -initial_specs.final_margin_top + 5).attr("width", "15")
        .attr("height", "15").attr("onclick", "window.location='" + data.detail_url + "';");
    return svg;
}

function graph_add_explanation_icon(icon_offset, svg, data, initial_specs){
    svg.append("svg:image").attr("xlink:href", "static/img/Gray_Info150.png").attr("class", "icon-15")
            .attr("x", x(max_x_val)+icon_offset).attr("y", -initial_specs.final_margin_top + 5).attr("width", "15")
            .attr("height", "15").attr("onclick", "show_explanation('" + data.explanation + "');");            
    return svg;
}

function graph_add_title(icon_offset, svg, data, initial_specs){
    svg.append("text")
        .attr("x", -initial_specs.margin_left).attr("y", -initial_specs.final_margin_top + 20)
        .attr("text-anchor", function (d) { return "start";  }  )
        .attr("class", "lightish chart-title-label " + initial_specs.chart_size)
        .text(data.title);
    return svg;
}

function graph_add_text(svg, data, initial_specs){
    
    res = svg.selectAll("label").data(data.text).enter().append("text")
        .attr("x", function(d){ return d.x; })
        .attr("y", function(d){ return d.y; })
        .attr("text-anchor", function (d) { return d.align;  }  )
        .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
        .text(function(d){ return d.text; });
    return svg;
}

function get_max_mins(){
    var min_x_val = null; var min_y_val = null; var max_x_val = null; var max_y_val = null;
    if('max_x' in data){
        min_x_val = data.min_x; max_x_val = data.max_x;
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
        min_y_val = data.min_y; max_y_val = data.max_y;
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
   
    return {min_x_val, min_y_val, max_x_val, max_y_val};
}

function horizontal_line(data, id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': false};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, data, arg_specs, arg_initial_specs);
    
    if(width <= 0){ return; }
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
    
    /* Create graph */
    var x = d3.scaleLinear().range([0, width]); var y = d3.scaleLinear().range([height, 0]);
    if(debug.on && debug.data){ console.log(data); }
    
    // ID the range of possible values
    let {min_x_val, min_y_val, max_x_val, max_y_val} = get_max_mins(data);
    if(debug.on && debug.spacing){ console.log("X: (" + min_x_val + ", " + min_y_val + ") Y: (" + max_x_val + "," + max_y_val + ")"); }
    
    // Set the domains
    x.domain([min_x_val, max_x_val]);
    
    if(initial_specs.flip){ y.domain([max_y_val, min_y_val]); }
    else{ y.domain([min_y_val, max_y_val]); }
    
    // Print shading if necessary
    if('shading_vars' in initial_specs && initial_specs.shading_vars != null){ svg = graph_add_shading_ranges(svg, data, x, y, initial_specs); }
    
    // Print any vertical lines, if necessary
    svg = graph_print_vertical_lines(svg, x, height, initial_specs);
    
    // Handle the X-Axis
    svg = graph_print_x_axis(svg, x, data, width, height, min_x_val, max_x_val, {'type': 'horizontal_line'}, initial_specs);
    
    // Handle the Y-Axis
    svg = graph_print_y_axis(svg, x, y, data, width, height, min_x_val, max_x_val, min_y_val, max_y_val, initial_specs);
    
    icon_offset = -15;
    // Add the link icon to see more
    if('detail_url' in data && data.detail_url != null){ svg = graph_add_link_icon(icon_offset, svg, data, initial_specs); icon_offset -= 20; }
    
    // Create the header section of the chart/tile
    if('explanation' in data && data.explanation != null){ svg = graph_add_explanation_icon(icon_offset, svg, data, initial_specs); icon_offset -= 20; }

    // Add the title
    if('title' in data){ svg = graph_add_title(svg, data, initial_specs); }
    
    // Add the legend if necessary
    if('legend' in data){ svg = graph_create_legend(svg, x, y, width, height, initial_specs, data); }
    if('shading_vars' in initial_specs && initial_specs.shading_vars != null){
        svg = graph_add_shading_legend(svg, x, data, height, min_x_val, max_x_val, initial_specs);
    }
    
    if('text' in data){ svg = graph_add_text(svg, data, initial_specs); }
    
    // Print the data
    var line = d3.line()
        .curve(d3.curveLinear)
        .x(function(d){ return x(d.x); }).y(function(d){ return y(d.y); });

    for(var a = 0;a<data.data.length;a++){
        tmp_data = data.data[a];
        
        svg.append("path")
          .datum(tmp_data.points)
          .attr("fill", "none") .attr("stroke", tmp_data['stroke'])
          .attr("stroke-linejoin", "round").attr("stroke-linecap", "round")
          .attr("stroke-dasharray", tmp_data['stroke-dasharray'])
          .attr("stroke-width", tmp_data['stroke-width'])
          .attr("d", line);
          
        // Add the balls if necessary
        if('ball_r' in tmp_data){
           
            svg.selectAll().data(tmp_data.points)
              .enter().append("circle").each(function(d){
                
                d.final_fill = ('ball_fill' in tmp_data) ? tmp_data.ball_fill : "#33F";
                d.final_stroke = ('ball_stroke' in tmp_data) ? tmp_data.ball_stroke : "#33F";
                
                if(initial_specs.highlight && d.highlight){ d.final_fill = initial_specs.highlight_color; } 
            }).attr("cx", function(d) { return x(d.x); })
              .attr("r", tmp_data.ball_r)
              .attr("cy", function(d) { return y(d.y); })
              .style("fill", function(d){ return d.final_fill; }).style("stroke", function(d){ return d.final_stroke; });
        }
    }
    
    
    
    // Add the slider if necessary
    if('slider' in data){ svg = graph_create_slider(svg, x, y, width, height, initial_specs, data); }
    
}

function spark_line(data, id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': false};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, data, arg_specs, arg_initial_specs);
    
    if(width <= 0){ return; }
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
    
    /* Create graph */
    var x = d3.scaleLinear().range([0, width]); var y = d3.scaleLinear().range([height, 0]);
    if(debug.on && debug.data){ console.log(data); }
    
    // ID the range of possible values
    let {min_x_val, min_y_val, max_x_val, max_y_val} = get_max_mins(data);
    if(debug.on && debug.spacing){ console.log("X: (" + min_x_val + ", " + min_y_val + ") Y: (" + max_x_val + "," + max_y_val + ")"); }
    
    // Set the domains
    x.domain([min_x_val, max_x_val]);
    
    if(initial_specs.flip){ y.domain([max_y_val, min_y_val]); }
    else{ y.domain([min_y_val, max_y_val]); }
    
    // Print the data
    var line = d3.line()
        .curve(d3.curveLinear)
        .x(function(d){ return x(d.x); }).y(function(d){ return y(d.y); });

    for(var a = 0;a<data.data.length;a++){
        tmp_data = data.data[a];
        
        svg.append("path")
          .datum(tmp_data.points)
          .attr("fill", "none") .attr("stroke", tmp_data['stroke'])
          .attr("stroke-linejoin", "round").attr("stroke-linecap", "round")
          .attr("stroke-dasharray", tmp_data['stroke-dasharray'])
          .attr("stroke-width", tmp_data['stroke-width'])
          .attr("d", line);
          
    }
    
}

function vertical_bars(data, id, arg_specs, arg_initial_specs = null){
    
    var debug = {'on': false, 'spacing': true, 'data': false};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, data, arg_specs, arg_initial_specs);
    
    if(width <= 0){ return; }
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
    
    
    per_bar_width = width/data.data[0].points.length;
    bandwidth = per_bar_width * .8; // Padding = .1
    bandwidth_offset = per_bar_width * .1;
    
    
    /* Create graph */
    
    var x = d3.scaleLinear().range([0, width - per_bar_width]);
    var y = d3.scaleLinear().range([height, 0]);
    if(debug.on && debug.data){ console.log("Data"); console.log(data); }
    
    // ID the range of possible values
    let {min_x_val, min_y_val, max_x_val, max_y_val} = get_max_mins(data);
    if(debug.on && debug.spacing){ console.log("X: (" + min_x_val + ", " + min_y_val + ") Y: (" + max_x_val + "," + max_y_val + ")"); }
    
    // Set the domains
    x.domain([min_x_val, max_x_val]);
    if(initial_specs.flip){ y.domain([max_y_val, min_y_val]); }
    else{ y.domain([min_y_val, max_y_val]); }
    
    if(debug.on && debug.spacing){ console.log("Per Bar: " + per_bar_width + " & w/ padding: " + bandwidth); }
    
    // Print shading if necessary
    if('shading_vars' in initial_specs && initial_specs.shading_vars != null){ svg = graph_add_shading_ranges(svg, data, x, y, initial_specs); }
    
    // Print any vertical lines, if necessary
    svg = graph_print_vertical_lines(svg, x, height, initial_specs);
    
    // Handle the X-Axis
    svg = graph_print_x_axis(svg, x, data, width, height, min_x_val, max_x_val, {'type': 'vertical_bars', 'bandwidth_offset': bandwidth_offset, 'bandwidth': bandwidth}, initial_specs);
    
    // Handle the Y-Axis
    svg = graph_print_y_axis(svg, x, y, data, width, height, min_x_val, max_x_val, min_y_val, max_y_val, initial_specs);
    
    icon_offset = -15;
    // Add the link icon to see more
    if('detail_url' in data && data.detail_url != null){ svg = graph_add_link_icon(icon_offset, svg, data, initial_specs); icon_offset -= 20; }
    
    // Create the header section of the chart/tile
    if('explanation' in data && data.explanation != null){ svg = graph_add_explanation_icon(icon_offset, svg, data, initial_specs); icon_offset -= 20; }

    // Add the title
    if('title' in data){ svg = graph_add_title(svg, data, initial_specs); }
    
    // Add any text
    if('text' in data){ svg = graph_add_text(svg, data, initial_specs); }
    
    // Add the legend if necessary
    if('legend' in data){ svg = graph_create_legend(svg, x, y, width, height, initial_specs, data); }
    if('shading_vars' in initial_specs && initial_specs.shading_vars != null){
        svg = graph_add_shading_legend(svg, x, data, height, min_x_val, max_x_val, initial_specs);
    }
    
    // Add the slider if necessary
    if('slider' in data){ svg = graph_create_slider(svg, x, y, width, height, initial_specs, data); }
    
    
    // Print the bars
    for(var a = 0;a<data.data.length;a++){
        tmp_data = data.data[a];
        
        
        var bars = svg.selectAll("bar").data(tmp_data.points)
          .enter().append("rect");
          
        bars.each(function(d){
            d.final_fill = initial_specs.fill;
            
            if(initial_specs.highlight && d.highlight){ d.final_fill = initial_specs.highlight_color; } 
        });
          
          
        bars.attr("class", "bar")
          .attr("x", function(d) { return x(d.x) + bandwidth_offset; })
          .attr("width", bandwidth)
          .attr("y", function(d) { return y(d.y); })
          .style("fill", function(d){ return d.final_fill; })
          .attr("height", function(d, i) { return height - y(d.y); });
          
        if('show_counts' in data && [null, false].indexOf(data.show_counts) == -1){
            for(var a = 0;a<tmp_data.points.length;a++){
                pt = tmp_data.points[a];
                if(y(d.y) + 10 > height){
                    pt.label_y = y(pt.y)-5; pt.color_class = "lightish";
                }
                else{
                    pt.label_y = y(pt.y) + 22; pt.color_class = "white";
                }
                pt.label_x = x(pt.x) + bandwidth/2 + bandwidth_offset;
            }
            
            svg.selectAll("bar").data(tmp_data.points)
                .enter().append("text").attr("text-anchor", "middle")
                .attr("class", function(d){ return d.color_class + " chart-tick-label " + initial_specs.chart_size; })
                .attr("x", function(d) { return d.label_x; }).attr("y", function(d) { return d.label_y; })
                .text(function(d) { return d[data.show_counts]; });
                
            svg.selectAll("bar").data(tmp_data.points)
                .enter().append("text").attr("text-anchor", "middle")
                .attr("class", function(d){ return d.color_class + " chart-tick-label " + initial_specs.chart_size; })
                .attr("x", function(d) { return d.label_x; }).attr("y", function(d) { return d.label_y - 12; })
                .text("n");
            
        }            
    }
    
    // Add the comparison line
    if('show_comparison_line' in data && [null, false].indexOf(data.show_comparison_line) == -1){ 
        var line = d3.line()
        .curve(d3.curveLinear)
        .x(function(d){ return x(d.x) + bandwidth/2 + bandwidth_offset; }).y(function(d){ return y(d[data.show_comparison_line]); });

        for(var a = 0;a<data.data.length;a++){
            tmp_data = data.data[a];
            
            svg.append("path")
              .datum(tmp_data.points)
              .attr("fill", "none") .attr("stroke", "orange")
              .attr("stroke-linejoin", "round").attr("stroke-linecap", "round")
              .attr("stroke-dasharray", "5,5")
              .attr("stroke-width", 3)
              .attr("d", line);
        }
    
    }
    
}

function horizontal_trainmap(data, id, arg_specs, arg_initial_specs = null){
    
    var debug = {'on': false, 'spacing': true, 'data': false};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, data, arg_specs, arg_initial_specs);
    
    if(width <= 0){ return; }
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
    
    
    per_bar_width = width/data.data[0].points.length;
    bandwidth = per_bar_width * .8; // Padding = .1
    bandwidth_offset = per_bar_width * .1;
    
    
    /* Create graph */
    
    var x = d3.scaleLinear().range([0, width - per_bar_width]);
    var y = d3.scaleLinear().range([height, 0]);
    if(debug.on && debug.data){ console.log("Data"); console.log(data); }
    
    // ID the range of possible values
    let {min_x_val, min_y_val, max_x_val, max_y_val} = get_max_mins(data);
    if(debug.on && debug.spacing){ console.log("X: (" + min_x_val + ", " + min_y_val + ") Y: (" + max_x_val + "," + max_y_val + ")"); }
    
    // Set the domains
    x.domain([min_x_val, max_x_val]);
    if(initial_specs.flip){ y.domain([max_y_val, min_y_val]); }
    else{ y.domain([min_y_val, max_y_val]); }
    
    if(debug.on && debug.spacing){ console.log("Per Bar: " + per_bar_width + " & w/ padding: " + bandwidth); }
    
    // Print shading if necessary
    if('shading_vars' in initial_specs && initial_specs.shading_vars != null){ svg = graph_add_shading_ranges(svg, data, x, y, initial_specs); }
    
    // Print any vertical lines, if necessary
    svg = graph_print_vertical_lines(svg, x, height, initial_specs);
    
    // Handle the X-Axis
    svg.append("line")
        .attr("x1", -initial_specs.margin_left).attr("x2", width + initial_specs.margin_right)
        .attr("y1", height/2).attr("y2", height/2)
        .style("stroke", "#AAA").style("fill", null);
    // Handle the Y-Axis
    svg = print_y_label(svg, data, initial_specs);
    
    icon_offset = -15;
    // Add the link icon to see more
    if('detail_url' in data && data.detail_url != null){ svg = graph_add_link_icon(icon_offset, svg, data, initial_specs); icon_offset -= 20; }
    
    // Create the header section of the chart/tile
    if('explanation' in data && data.explanation != null){ svg = graph_add_explanation_icon(icon_offset, svg, data, initial_specs); icon_offset -= 20; }

    // Add the title
    if('title' in data){ svg = graph_add_title(svg, data, initial_specs); }
    
    // Add any text
    if('text' in data){ svg = graph_add_text(svg, data, initial_specs); }
    
    // Add the legend if necessary
    if('legend' in data){ svg = graph_create_legend(svg, x, y, width, height, initial_specs, data); }
    if('shading_vars' in initial_specs && initial_specs.shading_vars != null){
        svg = graph_add_shading_legend(svg, x, data, height, min_x_val, max_x_val, initial_specs);
    }
    
    // Add the slider if necessary
    if('slider' in data){ svg = graph_create_slider(svg, x, y, width, height, initial_specs, data); }
    
    // Add the team labels
    if('show-data-labels' in data){
        svg = graph_add_data_labels(svg, x, y, width, height, {'type': 'horizontal_trainmap'}, initial_specs, data);
    }
    
    // Print the bubbles
    for(var a = 0;a<data.data.length;a++){
        tmp_data = data.data[a];
        
        
        var circles = svg.selectAll("circle").data(tmp_data.points)
          .enter().append("circle");
          
        circles.each(function(d){
            d.final_fill = initial_specs.fill;
            
            if(initial_specs.highlight && d.highlight){ d.final_fill = initial_specs.highlight_color; } 
        });
          
          
        circles.attr("class", "circle")
          .attr("cx", function(d) { return x(d.x); })
          .attr("r", function(d) { return d.radius; })
          .attr("cy", function(d) { return height/2; })
          .style("fill", function(d){ return d.final_fill; })
          .style("stroke", "#FFF");
    }
}

function create_pct_y_ticks(series, specs){
    var debug = true;
    var res = {'ticks': [], 'max': null, 'min':  null};
    max_eff = null; min_eff = null;
    for(var b = 0;b<series.length;b++){
        points = series[b].points;
        for(var a = 0;a<points.length;a++){
            var g = points[a];
            if(max_eff == null || max_eff < g.y){ max_eff = g.y; }
            if(min_eff == null || min_eff > g.y){ min_eff = g.y; }
        }
    }
    if('min' in specs && specs.min != null){ min_eff = specs.min; }
    if('max' in specs && specs.max != null){ max_eff = specs.max; }
    
    diff = max_eff - min_eff
    if(debug){ console.log("Eff Range: " + min_eff + " - " + max_eff + " ( diff=" + diff + ")"); }
    
    alt_min_eff = min_eff - diff*.2;
    alt_max_eff = max_eff + diff*.2;
    if(debug){ console.log("Alt Eff Range: " + alt_min_eff + " - " + alt_max_eff); }
    
    rounded_min_eff = null; rounded_max_eff = null; 
    extra = 0.0;
    while(rounded_min_eff == null || rounded_min_eff > min_eff){
        rounded_min_eff = Math.round((alt_min_eff - extra) * 100.0 / 10)/10;
        extra += .1;
    }
    extra = 0.0;
    while(rounded_max_eff == null || rounded_max_eff < max_eff){
        rounded_max_eff = Math.round((alt_max_eff + extra) * 100.0 / 10)/10;
        extra += .1;
    }
    if(rounded_min_eff == rounded_max_eff){
        rounded_max_eff += diff;
    }

    if(debug){ console.log("Rounded Eff Range: " + rounded_min_eff + " - " + rounded_max_eff); }
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

function create_numeric_y_ticks(series, specs = {}){
    var res = {'ticks': [], 'max': null, 'min':  null};
    max_eff = null; min_eff = null;
    for(var b = 0;b<series.length;b++){
        points = series[b].points;
        
        for(var a = 0;a<points.length;a++){
            var g = points[a];
            if(max_eff == null || max_eff < g.y){ max_eff = g.y; }
            if(min_eff == null || min_eff > g.y){ min_eff = g.y; }
        }
     
        if('shading_vars' in specs){
            for(var b = 0;b<specs.shading_vars.length;b++){
                var v = specs.shading_vars[b];
                for(var a = 0;a<points.length;a++){
                    var g = points[a];
                    if(max_eff == null || max_eff < g[v]){ max_eff = g[v]; }
                    if(min_eff == null || min_eff > g[v]){ min_eff = g[v]; }
                }
            }
        }
    }
    
    inc = (max_eff - min_eff) * .05;
    //console.log("Numeric inc: " + inc);
    alt_min_eff = min_eff - inc;
    alt_max_eff = max_eff + inc;
    //console.log("Alt Eff Range: " + alt_min_eff + " - " + alt_max_eff);
    rounded_min_eff = null; rounded_max_eff = null;
    rounding_factor = null;
    if(inc < 1){
        rounding_factor = 1;
    }
    else if (inc < 5){
        rounding_factor = 20;
    }
    else{
        rounding_factor = 50;
    }
    
    extra = 0.0;
    while(rounded_max_eff == null || rounded_max_eff < max_eff){
        rounded_max_eff = Math.round(alt_max_eff/rounding_factor + extra)*rounding_factor;
        extra += .01;
    }
    extra = 0.0;
    while(rounded_min_eff == null || rounded_min_eff > min_eff){
        rounded_min_eff = Math.round(alt_min_eff/rounding_factor - extra)*rounding_factor;
        extra += .01;
    }
        
    //console.log("Rounded Eff Range: " + rounded_min_eff + " - " + rounded_max_eff);
    diff = rounded_max_eff - rounded_min_eff;
    var num_ticks = 5;
    
    if(diff <= 10){ num_ticks = 5; }
    else if(diff <= 20){ num_ticks = 5; }
    else if(diff <= 30){ num_ticks = 4; }
    else if(diff <= 40){ num_ticks = 5; }
    else if(diff <= 50){ num_ticks = 6; }
    else if(diff <= 60){ num_ticks = 7; }
    else if(diff <= 70){ num_ticks = 8; }
    else if(diff <= 80){ num_ticks = 5; }
    else if(diff <= 90){ num_ticks = 7; }
    else if(diff <= 100){ num_ticks = 6; }
    
    
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

function create_game_x_ticks(series){
    var res = {'ticks': [], 'max': null, 'min':  null};
    var used_labels = [];
    
    var long_series_ID = null;
    var longest_series= null;
    for(var b = 0;b<series.length;b++){
        points = series[b].points;
        if(long_series_ID == null || longest_series < points.length){
            long_series_ID = b; longest_series = points.length;
        }
        
        for(var a = 0;a<points.length;a++){
            tick = points[a];
            if(res.min == null || res.min > tick.x){ res.min = tick.x; }
            if(res.max == null || res.max < tick.x){ res.max = tick.x; }
        }
        
            
        for(var a = 0;a<points.length;a++){ var g = points[a];
            if(used_labels.indexOf(g.label) == -1 && g.label != ""){ res.ticks.push({'x': g.x, 'label': g.label}); used_labels.push(g.label); }
        }
        //data['x_ticks'] = [{'x': 1, 'label': "G1"}, {'x': 2, 'label': "G2"}, {'x': 3, 'label': "G3"}, {'x': 4, 'label': "G4"}]
        
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
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, misc, arg_specs, arg_initial_specs);
    
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

function graph_create_legend(svg, x, y, width, height, initial_specs, data){
    legend = data.legend;
    start_loc_x = -initial_specs.margin_left + 5;
    start_loc_y = height + initial_specs.margin_bottom + (initial_specs.chart_size == "small" ? 0 : -3 );
    
    for(var a = 0;a<legend.items.length;a++){
        var item = legend.items[a];
        item.loc_x = start_loc_x;
        item.loc_y = start_loc_y;
        icon_w = 0;
        
        if(item.icon_type == "line"){
            icon_w = 20;
            icon_h = 20;
            svg.append("line")
            .attr("x1", item.loc_x + 2).attr("y1", item.loc_y - 2)
            .attr("x2", item.loc_x + 20).attr("y2", item.loc_y - 2)
            .attr("stroke", item.color).attr("stroke-dasharray", item['stroke-dasharray']).attr("stroke-width", item['stroke-width']);
        }
        if(item.icon_type == "rect"){
            icon_w = 25;
            icon_h = icon_w/1.61803398875;
            svg.append("rect")
            .attr("width", icon_w).attr("height", icon_h)
            .attr("x", item.loc_x - 5).attr("y", item.loc_y - 10)
            .attr("fill", item.fill);
        }
        if(item.icon_type == "circle"){
            icon_w = 15; 
            r = 5;
            icon_h = icon_w;
            svg.append("circle")
            .attr("r", r)
            .attr("cx", item.loc_x + r*2).attr("cy", item.loc_y - r)
            .attr("fill", item.fill).attr("stroke", item.stroke);
        }
        
        
        item.object = svg.append("text")
        .attr("x", item.loc_x + icon_w + 5).attr("y", item.loc_y)
        //.attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
        .attr("class", "font-11").attr("font-family", "Arial")
        .text(item.label)
        .attr("width", function(d){ return this.getComputedTextLength(); });
        
        item.width = parseFloat(item.object.attr("width"));
        
        if(legend.layout == "horizontal"){
            start_loc_x += item.width + icon_w + 10;
        }
        else if(legend.layout == "vertical"){
            start_loc_y += icon_h;
        }
        
    }
    return svg;
}

function graph_create_slider(svg, x, y, width, height, initial_specs, data){
    slider = data.slider;
    svg = display_slider(slider, svg, initial_specs);
    /*
    start_loc_x = -initial_specs.margin_left + 5;
    start_loc_y = height + initial_specs.margin_bottom - 10;
    
    for(var a = 0;a<legend.items.length;a++){
        var item = legend.items[a];
        item.loc_x = start_loc_x;
        item.loc_y = start_loc_y;
        icon_w = 0;
        
        if(item.icon_type == "line"){
            icon_w = 20;
            icon_h = 20;
            svg.append("line")
            .attr("x1", item.loc_x + 2).attr("y1", item.loc_y - 2)
            .attr("x2", item.loc_x + 20).attr("y2", item.loc_y - 2)
            .attr("stroke", item.color).attr("stroke-dasharray", item['stroke-dasharray']).attr("stroke-width", 2);
        }
        
        item.object = svg.append("text")
        .attr("x", item.loc_x + 25).attr("y", item.loc_y)
        //.attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
        .attr("class", "font-11").attr("font-family", "Arial")
        .text(item.label)
        .attr("width", function(d){ return this.getComputedTextLength(); });
        
        item.width = parseFloat(item.object.attr("width"));
        
        if(legend.layout == "horizontal"){
            start_loc_x += item.width + icon_w + 10;
        }
        else if(legend.layout == "vertical"){
            start_loc_y += icon_h;
        }
        
    }*/
    return svg;
}

function graph_add_data_labels(svg, x, y, width, height, chart_type, initial_specs, data){
    
    function overlap(locs){
        time_log.push({'tag': "Detect overlapping labels", 'start': new Date().getTime()});
    
        var solution = null; var found_overlap = null;

        attempts = 0;
        while(attempts < 1000 && (found_overlap == null || found_overlap == true)){
            found_overlap = false;
            for(var a = 0;a<locs.length;a++){
                loc = locs[a];
                if(attempts == 0) { // If it's the first time through, just try and default values
            
                    loc.y = loc.cy;
                
                }
                else if(attempts == 1) { // If it's the first time through, just try a standard up and down shift
                    rnd = Math.random();
                    sign = (a % 2 == 0) ? 1 : -1;
                    adj_rnd = .25;
                    loc.y_offset = height * adj_rnd * sign;
                    loc.y = height/2 + 7 + loc.y_offset;
                }
                else if(attempts < 50) { // If it's the first time through, just try a standard up and down shift
                    rnd = Math.random(); 
                    sign = (a % 2 == 0) ? 1 : -1;
                    adj_rnd = .15 + rnd*.25;
                    loc.y_offset = height * adj_rnd * sign;
                    loc.y = height/2 + 7 + loc.y_offset;
                }
                else{
                    
                    rnd = Math.random();
                    sign = (a % 2 == 0) ? 1 : -1;
                    adj_rnd = .10 + rnd*.36;
                    loc.y_offset = height * adj_rnd * sign;
                    loc.y = height/2 + 7 + loc.y_offset;
                }
            }    
            for(var a = 0;a<locs.length;a++){
                loc = locs[a];
                
                for(var b = 0;b<locs.length;b++){if(a != b){
                    loc_b = locs[b];
                    
                    //console.log(loc.display, zFormat(loc.y), loc.h, "vs", loc_b.display, zFormat(loc_b.y), loc_b.h);
                    if(loc.y + loc.h < loc_b.y - 10){ // It's above the other label completely
                        //console.log("  A");
                    }
                    else if(loc.y > loc_b.y + loc_b.h + 10){ // It's below the other label
                        //console.log("  B");
                    }
                    else{ // We need to check whether it's overlapping on the x since it could be on the y
                        //console.log("Possible overlap " + loc.display + " & " + loc_b.display);
                        if(loc.cx + loc.w < loc_b.cx - 10){ // It's fully to the left
                        
                        }
                        else if(loc.cx > loc_b.cx + loc_b.w + 10){ // It's fully to the right
                        
                        }
                        else{
                            //console.log("  Yep, " + loc.display + " is overlapping with " + loc_b.display);
                            found_overlap = true; break
                        }
                    }
                }}
                if(found_overlap){ break; }
            }
            attempts += 1; 
            //console.log("Done attempt " + attempts);
        }
        
        if(found_overlap){ solution = null; console_log({'msg': "No data-labels solution found..."}); }
        else{ solution = locs; }
        
        time_log[time_log.length-1].end = new Date().getTime();
        return solution;
    }
    
    tag = data['show-data-labels']
    locs = [];
    for(var a = 0;a<data.data.length;a++){
        var pts = data.data[a].points;
        
        for(var b = 0;b<pts.length;b++){
            pt = pts[b];
            pt.y_offset = ((b%2 == 0) ? height * .25 : height * -.25) + 7;
            
            pt.x_offset = 0;
            
            pt.object = svg.append("text")
                .attr("x", x(pt.x) + pt.x_offset).attr("y", height*.5 + pt.y_offset)
                //.attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                .attr("class", "graph-data-label font-11").attr("font-family", "Arial")
                .attr("text-anchor", "middle" )
                .text(pt[tag] + ": " + pt.val_str)
                .attr("width", function(d){ return this.getComputedTextLength(); });
            pt.w = parseFloat(pt.object.attr("width"));
            pt.cx = parseFloat(pt.object.attr("x"));
            pt.cy = parseFloat(pt.object.attr("y"));
            pt.h = 14;
        
            locs.push(pt);
        }
        
        
        
    }
    
    svg.selectAll(".graph-data-label").remove();
    if(overlap(locs) != null){
        // Remove the labels?
        
        for(var b = 0;b<locs.length;b++){
            pt = locs[b];
            pt.cy = pt.y;
           
            svg.append("text")
                .attr("x", x(pt.x) + pt.x_offset).attr("y", pt.y)
                //.attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
                .attr("class", "graph-data-label font-11").attr("font-family", "Arial")
                .attr("text-anchor", "middle" )
                .text(pt[tag] + ": " + pt.val_str)
            ;
            
            svg.append("line")
                .attr("x1", x(pt.x) + pt.x_offset)
                .attr("x2", x(pt.x) + pt.x_offset)
                .attr("y1", function(d){ if(pt.y < height/2){ return pt.y + 10; } else { return pt.y - 20; } } )
                    .attr("y2", height/2)
                .style("stroke", "#AAA").style("fill", null)
            ;
            
        }
        
    }
    return svg;
}

function custom_conditional_RPI_tile(misc, id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': false};
    
    var games = misc.data.future_games.filter(gm => gm.avg_RPI_with_win != null);
    
    row_height = 29;
    calc_height = 65 + row_height * games.length;
    
    arg_specs.height = calc_height;
    
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, misc, arg_specs, arg_initial_specs);
    if(width <= 0){ return; }
    
    var cur_projected_RPI = misc.data.sim_results[misc.data.sim_results.length-1].y
    var cur_projected_RPI_str = Math.round(cur_projected_RPI);
    
    
    var min_x_val = null;
    var max_x_val = null;
    
    
    if(games.length == 0){
        min_x_val = 0;
        max_x_val = cur_projected_RPI_str*2;
    }
    
    for(var a=0;a<games.length;a++){
        var gm = games[a];
        gm.height = row_height * a + 30;
        gm.diff = gm.avg_RPI_with_loss - gm.avg_RPI_with_win;
        
        if(min_x_val == null || min_x_val > gm.avg_RPI_with_loss){ min_x_val = gm.avg_RPI_with_loss; }
        if(min_x_val == null || min_x_val > gm.avg_RPI_with_win){ min_x_val = gm.avg_RPI_with_win; }
        if(max_x_val == null || max_x_val < gm.avg_RPI_with_loss){ max_x_val = gm.avg_RPI_with_loss; }
        if(max_x_val == null || max_x_val < gm.avg_RPI_with_win){ max_x_val = gm.avg_RPI_with_win; }
    }
    
    
    
    var x = d3.scaleLinear().range([120, width-30]);
    var y = d3.scaleLinear().range([height, 0]);
    x.domain([min_x_val, max_x_val]);
    y.domain([0, height]);
    
    
    
    svg.append("text")
            .attr("x", x(cur_projected_RPI_str)).attr("y", height-20)
            .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
            .attr("text-anchor", function (d) { return "middle";  }  )
            .text("Current Projected RPI: " + zFormat(cur_projected_RPI_str, 0));
    
    
    // Header
    svg.append("text")
        .attr("x", 10).attr("y", 15)
        .attr("text-anchor", function (d) { return "start";  }  )
        .attr("class", "lightish chart-axis-label bold " + initial_specs.chart_size)
        .text("Opponent"); 
    svg.append("text")
        .attr("x", x(cur_projected_RPI_str) - 20).attr("y", 15)
        .attr("text-anchor", function (d) { return "end";  }  )
        .attr("class", "lightish chart-axis-label bold " + initial_specs.chart_size)
        .text("Proj w/ W"); 
    svg.append("text")
        .attr("x", x(cur_projected_RPI_str) + 20).attr("y", 15)
        .attr("text-anchor", function (d) { return "start";  }  )
        .attr("class", "lightish chart-axis-label bold " + initial_specs.chart_size)
        .text("Proj w/ L"); 
            
    svg.append("line")
            .attr("x1", 5).attr("y1", 22)
            .attr("x2", width-5).attr("y2", 22)
            .style("stroke-width", 1.5).style("stroke", "rgb(133, 133, 133)").style("fill", "none");
    
    
    // Legend
    for(var a=0;a<games.length;a++){
        var gm = games[a];
        
        
        cur_x = x(cur_projected_RPI_str);
        win_x = x(gm.avg_RPI_with_win);
        loss_x = x(gm.avg_RPI_with_loss);
        
        
        svg.append("text")
            .attr("x", 10).attr("y", gm.height + 27)
            .attr("text-anchor", function (d) { return "start";  }  )
            .attr("class", "lightish chart-axis-label " + initial_specs.chart_size)
            .text(gm.opp_short_code); 
            
        // Print the full range rect
        svg.append("rect")
            .attr("x", x(gm.avg_RPI_with_win))
            .attr("y", gm.height + 15)
            .attr("width", loss_x - win_x)
            .attr("height", 10)
            .style("fill", "#FFF")
            .style('stroke', '#888');
        
        // Print the win rect
        svg.append("rect")
            .attr("x", x(gm.avg_RPI_with_win) + 1)
            .attr("y", gm.height + 15 + 1)
            .attr("width", function(){ if(win_x > cur_x){ return win_x - cur_x - 1; } else{ return cur_x - win_x - 1; } })
            .attr("height", 8)
            .attr("class", "green");
            
        // Print the loss rect
        svg.append("rect")
            .attr("x", x(cur_projected_RPI_str) + 1)
            .attr("y", gm.height + 15 + 1)
            .attr("width", loss_x - cur_x - 1)
            .attr("height", 8)
            .attr("class", "red");
            
        svg.append("text")
            .attr("x", x(gm.avg_RPI_with_loss) + 5).attr("y", gm.height + 23)
            .attr("text-anchor", function (d) { return "start";  }  )
            .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
            .text(gm.avg_RPI_with_loss_str);  
            
        svg.append("text")
            .attr("x", 
                function(){ 
                    if(win_x > cur_x){ return x(gm.avg_RPI_with_win); } 
                    else{ return x(gm.avg_RPI_with_win) - 5; } 
            
                }
            )
            .attr("y", 
                function(){ 
                    if(win_x > cur_x){ return gm.height + 10; } 
                    else{ return gm.height + 23; } }
            )
            .attr("text-anchor", function (d) { if(win_x > cur_x){ return "start"; } else{ return "end"; }  }  )
            .attr("class", "lightish chart-tick-label " + initial_specs.chart_size)
            .text(gm.avg_RPI_with_win_str);  
        
    }
    
    svg.append("line")
            .attr("x1", x(cur_projected_RPI_str)).attr("y1", 35)
            .attr("x2", x(cur_projected_RPI_str)).attr("y2", height-35)
            .style("stroke-width", 1.5).style("stroke", "rgb(173, 173, 173)").style("fill", "none").style('stroke-dasharray', '2,2');
    
    if(debug.on && debug.spacing){
        console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height));
    }
    
}

function custom_next_game_tile(misc, id, arg_specs, arg_initial_specs = null){
   
    var debug = {'on': false, 'spacing': true, 'data': false};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, misc, arg_specs, arg_initial_specs);
    
    var tags = [];
    tags.push({'label': 'Off', 'var': 'off_efficiency'});
    tags.push({'label': 'Def', 'var': 'def_efficiency_inverted'});
    tags.push({'label': 'FO%', 'var': 'faceoff_win_rate'});
    
    
    var game_list = misc.data.next_game.history.filter(gm => gm.this_year);
    var num_games = game_list.length;
    
    for(var a = 0;a<num_games;a++){
        
        var game = game_list[a];
        
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
    header += "<div id='next_game_header_row' class='bbottom flex no-padding' style='margin-top:0px; margin-bottom: 3px;'>";
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

function spark_bar(id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': true};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, null, arg_specs, arg_initial_specs);
    
    if(width <= 0){ return; }
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
   
    
    if('show_border' in initial_specs){
        svg.append("rect")
            .attr("x", 0).attr("y", 0)
            .attr("width", width).attr("height", specs.height)
            .attr("rx", 3).attr("ry", 3)
            .attr('id', id + "-spark-bar-div")
            .style("fill", specs.bar_fill)
            .attr("class", "spark-bar-background");
    }
    
    svg.append("rect")
		.attr("x", 1).attr("y", 1)
		.attr("width", specs.bar_width*width - 2).attr("height", specs.height-2)
		.attr("rx", 1).attr("ry", 1)
		.attr('id', id + "-spark-bar")
        .style("fill", specs.fill).style("stroke-width", 0)
		.attr("class", "spark-bar-fill");
        
    if(specs.bar_width < 1.0){
        svg.append("rect")
            .attr("x", specs.bar_width*width - 2).attr("y", 1)
            .attr("width", 1).attr("height", specs.height-2)
            .attr('id', id + "-spark-bar")
            .style("fill", specs.fill).style("stroke-width", 0)
            .attr("class", "spark-bar-fill");
    }
    
    // Add data labels if necessary
    if('label' in initial_specs && initial_specs.label != null){
        anchr = "end"; clr = "white";
        label = svg.append("text").attr("text-anchor", anchr )
            .attr("x", specs.bar_width*width - 5).attr("y", specs.height - 4)
            .attr("font-size", 10).attr("font-family", "Arial").style("fill", clr).style("opacity", 0)
            .text(initial_specs.label);
            
        if(specs.bar_width < .25){
            anchr = "start"; clr = "#666";
            label.attr("x", specs.bar_width*width + 2).attr("text-anchor", anchr ).style("fill", clr);
        }
        label.style("opacity", 1);
    }
    
}
function comparison_bar(id, arg_specs, arg_initial_specs = null){
    var debug = {'on': false, 'spacing': true, 'data': true};
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, null, arg_specs, arg_initial_specs);
    
    if(width <= 0){ return; }
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
   
    
    var better = (specs.value > specs.comp_value);

    var gap = Math.abs(specs.value - specs.comp_value);
    
    
    if(better){
        
        svg.append("rect")
            .attr("x", 0).attr("y", 0)
            .attr("width", specs.value * width).attr("height", specs.height)
            .attr("rx", 3).attr("ry", 3)
            .attr('id', id + "-spark-bar-div")
            .style("fill", "#88F")
            .attr("class", "spark-bar-background");
            
        svg.append("line")
            .attr("x1", specs.comp_value * width).attr("y1", 1)
            .attr("x2", specs.comp_value * width).attr("y2", specs.height - 1)
            .style("stroke", "#FFF").style("stroke-width", 2);
            
        // Add data labels if necessary
        if('show_labels' in initial_specs && initial_specs.show_labels != null){
            label = svg.append("text").attr("text-anchor", "start" )
            .attr("x", specs.value * width + 3).attr("y", specs.height - 2)
            .attr("font-size", 10).attr("font-family", "Arial").style("fill", "#666")
            .text(initial_specs.label);
            
            if(gap < .2){
                if(specs.comp_value > .2){
                    comp_label = svg.append("text").attr("text-anchor", "end" )
                    .attr("x", specs.comp_value * width - 3).attr("y", specs.height - 2)
                    .attr("font-size", 10).attr("font-family", "Arial").style("fill", "#FFF")
                    .text(initial_specs.comp_label);
                }
                else{ 
                    // There wouldn't be enough room to squeeze it in
                }
            }
            else{
                
                comp_label = svg.append("text").attr("text-anchor", "start" )
                .attr("x", specs.comp_value * width + 3).attr("y", specs.height - 2)
                .attr("font-size", 10).attr("font-family", "Arial").style("fill", "#FFF")
                .text(initial_specs.comp_label);
            }
        }
    }
    else{
        svg.append("rect")
            .attr("x", 0).attr("y", 0)
            .attr("width", specs.comp_value * width).attr("height", specs.height)
            .attr("rx", 3).attr("ry", 3)
            .attr('id', id + "-spark-bar-div")
            .style("fill", "#FFF").style("stroke", "#88F")
            .attr("class", "spark-bar-background");
            
        svg.append("rect")
            .attr("x", 0).attr("y", 1)
            .attr("width", specs.value*width - 2).attr("height", specs.height-2)
            .attr("rx", 1).attr("ry", 1)
            .attr('id', id + "-spark-bar")
            .style("fill", specs.fill).style("stroke-width", 0)
            .attr("class", "spark-bar-fill");
            
        // Add data labels if necessary
        if('show_labels' in initial_specs && initial_specs.show_labels != null){
            comp_label = svg.append("text").attr("text-anchor", "start" )
            .attr("x", specs.comp_value * width + 3).attr("y", specs.height - 2)
            .attr("font-size", 10).attr("font-family", "Arial").style("fill", "#666")
            .text(initial_specs.comp_label);
            
            if(gap < .2){
                if(specs.value > .2){
                    label = svg.append("text").attr("text-anchor", "end" )
                    .attr("x", specs.value * width - 3).attr("y", specs.height - 2)
                    .attr("font-size", 10).attr("font-family", "Arial").style("fill", "#FFF")
                    .text(initial_specs.label);
                }
                else{ 
                    // There wouldn't be enough room to squeeze it in
                }
            }
            else{
                
                label = svg.append("text").attr("text-anchor", "start" )
                .attr("x", specs.value * width + 3).attr("y", specs.height - 2)
                .attr("font-size", 10).attr("font-family", "Arial").style("fill", "#666")
                .text(initial_specs.label);
            }
        }
    }
    
    
       
   
    
    
    
}
function display_slider(slider, svg, initial_specs){
	
    function pct_to_loc(pct, specs){
        var loc = null;
        var comp = null;
        if(specs.orientation == "horizontal"){
            comp = specs.width;
        }
        else{
            comp = specs.height;
        }
        loc = pct*comp;
        return loc;
    }
    id = slider.id;
    specs = slider;
    if(!('stops' in specs)){ specs.stops = 10; }
	
    val = 5;
	
    height = specs.height; 
    width = specs.width;
    event_var = null;
    if(specs.orientation == "vertical"){
        circle_x = width/2;
        circle_y = height/2;
        event_var = "y"
        max_loc = height + specs.loc_y; min_loc = specs.loc_y;
        specs.inc = (specs.height-specs.stops)/(specs.stops-1);
	
    }
    else if(specs.orientation == "horizontal"){
        circle_x = specs.loc_x + pct_to_loc(specs.pct_loc, specs);
        circle_y = specs.loc_y + specs.height/2;
        event_var = "x"
        max_loc = width + specs.loc_x; min_loc = specs.loc_x;
        specs.inc = (specs.width-specs.stops)/(specs.stops-1);
    }
    
    if('start_label' in specs && [null, ''].indexOf(specs.start_label) == -1){
        var end_point_labels = []
        var epl = {'label': specs.end_label};
        var spl = {'label': specs.start_label};
        end_point_labels.push(spl);end_point_labels.push(epl);
        if(specs.orientation == "vertical"){
            spl.anchor = elp.anchor = "middle";
            
        }
        else{
            spl.anchor = "end"; epl.anchor = "start";
            spl.y = epl.y = circle_y + 3;
            spl.x = specs.loc_x - 10;
            epl.x = specs.loc_x + width + 10;
        }
        svg.selectAll("label").data(end_point_labels).enter().append("text")
            .attr("text-anchor", function (d) { return d.anchor;  }  )
            .attr("y", function(d){return d.y;}).attr("x", function(d){return d.x;})
            .text(function(d){  return d.label; })
            .attr("class", "label lightish chart-tick-label small");
        
    }
    
    
    // Display labels if there are labels to display
	/*for(var a = 10;a>0;a--){
		svg.append("text")
		.attr("class", "label").attr("text-anchor", function (d) { return text_anc;  }  )
		.attr("y", height - inc*(a-1) + 0)
		.attr("x", num_offset)
		.text(a)
		.style('font-size', function(d) {  return (10) + 'px'; })
		.style('font-family', function(d) { return "Arial, sans-serif"; } )
		.style('font-weight', function(d) { return "700"; } )
		;
    
	}
	*/
    
	// Display the outer rectangle of the slider
	svg.append("rect")
		.attr("x", specs.loc_x).attr("y", specs.loc_y)
		.attr("width", width).attr("height", height)
		.attr("rx", 4)
		.attr("ry", 4)
		.attr('id', id + "-slider")
		.attr("class", "slider-background");
	
    if('show_value_on_drag' in specs && specs.show_value_on_drag){
        
        svg.append("rect")
            .attr("x", circle_x - 30).attr("y", circle_y + 10 - 50)
            .attr("rx", 4).attr("ry", 4)
            .attr("width", 60).attr("height", 30)
            .attr('id', id + "-overlay")
            .attr("class", "slider-overlay hidden");
        
        svg.append("text").attr("text-anchor", "middle")
            .attr("x", circle_x).attr("y", circle_y + 30 - 50)
            .attr('id', id + "-overlay-text")
            .text('')
            .attr("class", "label lightish chart-tick-label small hidden");
        
    }
	// ID where the slider is (and where the light color will take over)
	/*y_loc = val / specs.stops * height;
	y_val = height - y_loc - 6;
    */
    
    
    // Add the end of the slider (rounded) clear fill
	svg.append("rect")
		.attr("x", circle_x + 1).attr("y", specs.loc_y+1)
		.attr("width", specs.loc_x + width - circle_x - 2).attr("height", height-2)
		.attr("rx", 6)
		.attr("ry", 6)
		.attr('id', 'rect_' + id + '_primary')
		.style("fill", "#FFF");
    
    
	// Add the middle of the slider (non-rounded) clear fill
    /*svg.append("rect")
		.attr("x", x_offset + 1).attr("y", y_loc)
		.attr("width", 8).attr("height", 15)
		.attr('id', 'rect_' + id + '_cap')
		.style("fill", "#FFF");
	*/
	
    // Add the slider ball
	svg.append("circle")
		.attr("cx", circle_x).attr("cy", circle_y)
        .attr("width", width)
        .attr('offset_x', specs.loc_x).attr('offset_y', specs.loc_y)
        .attr("height", height)
        .attr("orientation", specs.orientation)
		.attr("r", 7)
		.style("fill", "#AAA").attr('id', id)
		.call(d3.drag().on("start", slider.dragStarted).on("drag", slider.drag).on("end", slider.dragEnded));
	
   
    return svg;
}


function display_toggle(toggle, id, arg_specs, arg_initial_specs = null){
	var debug = {'on': false, 'spacing': true, 'data': false};
    

    arg_specs.margin_left = arg_specs.margin_top = arg_specs.margin_right = arg_specs.margin_bottom = 0;
    arg_specs.width = toggle.start_x + toggle.end_x + 10 + arg_specs.height*2;
    let {width, height, specs, initial_specs, svg} = initiate_svg(id, null, arg_specs, arg_initial_specs);
    
    
    if(debug.on && debug.spacing){ console.log("SVG Width x Height: " + rnd(width) + " x " + rnd(height)); }
    
    height = specs.height; 
    width = specs.width;
    toggle_width = height*2;
    toggle_x = toggle.start_x + (width - toggle.start_x - toggle.end_x - toggle_width)/2;
    
    extra_class = "";
    if('class' in specs){ extra_class = specs.class; }
    val = 0;
    
    event_var = null;
    circle_x = 0 + height/2;
    circle_y = height/2;
    event_var = "x"

    
    var end_point_labels = []
    var epl = {'label': toggle.end_label};
    var spl = {'label': toggle.start_label};
    end_point_labels.push(spl);end_point_labels.push(epl);
    epl.anchor = "end"; spl.anchor = "start";
    spl.y = epl.y = circle_y + 3;
    spl.x = 1;
    epl.x = width - 1;
    label_width = 0.0;
    for(var a = 0;a<end_point_labels.length;a++){
        item = end_point_labels[a];

        item.object = svg.append("text")
        .attr("x", item.x).attr("y", item.y)
        .attr("text-anchor", item.anchor  )
        //.attr("class", 'lightish chart-tick-label ' + initial_specs.chart_size)
        .attr("class", 'font-11').attr("font-family", "Arial")
        .text(item.label);

        
    }   
    
    
    
	// Display the outer rectangle of the slider
	svg.append("rect")
		.attr("x", toggle_x).attr("y", 0)
		.attr("width", toggle_width).attr("height", height)
		.attr("rx", (height/2))
		.attr("ry", (height/2))
		.attr('id', id + "-toggle-background")
		.attr("class", extra_class + " toggle-background" + (toggle.val ? " set" : ""));
	

	
	
    // Add the slider ball
    
	svg.append("circle")
		.attr("cx", toggle_x + height/2 + (toggle.val ? height : 0)).attr("cy", circle_y)
        .attr("width", width)
        .attr("height", height)
        .attr("nonce", toggle.val)
		.attr("r", (height/2)-1)
		.attr('id', id)
        .attr("class", extra_class + " toggle-ball" +  (toggle.val ? "" : " set"))
        //.on('click', d3toggle_click)
        .on('click', toggler);
	
   
    return svg;
}

