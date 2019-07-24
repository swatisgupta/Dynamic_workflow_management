$(document).ready(function(){

function ConvertFormToJSON(form){
    var array = jQuery(form).serializeArray();
    var json = {};
    
    jQuery.each(array, function() {
        json[this.name] = this.value || '';
    });
    
    return json;
}

//setInterval(update_status, 800);
setInterval(update_status, 3000);

function update_status() {
 $("#current-pipelines").tabulator("setData", "http://localhost:9000/?q=getstatus");
 $("#server-response").text("");
}

$("#current-pipelines").tabulator({
    height:"311px",
    layout:"fitColumns",
    resizableColumns:false,
    columns:[
        {title:"Pipeline", field:"pipe_name"},
        {title:"Total Processes", field:"total_procs"},
    ],
    rowFormatter:function(row){
        //create and style holder elements
       var holderEl = $("<div></div>");
       var tableEl = $("<div></div>");

       holderEl.css({
           "box-sizing":"border-box",
           "padding":"10px 30px 10px 10px",
           "border-top":"1px solid #333",
           "border-bottom":"1px solid #333",
           "background":"#ddd",
       })

       tableEl.css({
           "border":"1px solid #333",
       })

       holderEl.append(tableEl);

       row.getElement().append(holderEl);

       //create nested table
       tableEl.tabulator({
           layout:"fitColumns",
           data:row.getData().running_components,
           columns:[
               {title:"Component name", field:"comp_name"},
               {title:"Processes used", field:"procs_used"},
               {title:"arguments", field:"args"},
           ],
           rowClick:function(e, row){
        //e - the click event object
        //row - row component
                $("#compname").val(row.getData().comp_name);
                $("#args").val(row.getData().args);

            },
       })
    },
    rowClick:function(e, row){
        //e - the click event object
        //row - row component
        $("#pipe").val(row.getData().pipe_name);

    },
});

$("refresh-status").click(function(){
    $("#current-pipelines").tabulator("setData", "http://localhost:9000/?q=getstatus");
});

$("#form1").submit(function(event){
    event.preventDefault();
    $.ajax({
           url : 'http://localhost:9000/',
           type : "POST",
           //dataType : 'json',
           data : JSON.stringify(ConvertFormToJSON(this)),
           
           success : function(data) {
              $("#server-response").text(JSON.stringify(data));
           },

           //error: function(jqXhr, textStatus, errorThrown){
           //    console.log(errorThrown);
           //} 

    })   
});

});
