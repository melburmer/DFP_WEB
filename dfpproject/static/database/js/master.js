// Dynamic region field load by using ajax
$("#ProjectField").change(function () {
  var url = $("#InsertRecordForm").attr("data-regions-url");  // get the url of the `load_regions` view
  var project = $(this).val();  // get the selected project from the HTML input

  $.ajax({                       // initialize an AJAX request
    url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
    data: {
      'project': project       // add the project to the GET parameters
    },
    success: function (data) {   // `data` is the return of the `load_regions` view function
      $("#RegionField").html(data);  // replace the contents of the regions input with the data that came from the server
    }
  });

});

// load acts
$("#UsecaseField").change(function () {
  var url = $("#InsertRecordForm").attr("data-acts-url");
  var fo_use_case = $(this).val();


  $.ajax({                       // initialize an AJAX request
    url: url,
    data: {
      'fo_use_case': fo_use_case       // add the fo_use_case to the GET parameters
    },
    success: function (data) {
      $("#ActField").html(data);
    }
  });

});


// load act specifications


$("#ActField").change(function () {

  var url = $("#InsertRecordForm").attr("data-actspecs-url");
  var activity = $(this).val();

  $.ajax({                       // initialize an AJAX request
    url: url,
    data: {
      'activity': activity       // add the act to the GET parameters
    },
    success: function (data) {
      $("#ActSpeField").html(data);
    }
  });

});

$("#RecordTypeField").on('change', function () {

    if (this.value == 'alarm_triggered')
    {
      $('#RemoveHeaderField').parent().show() // show label
      $("#RemoveHeaderField").show(); // show checkbox
    }
    else{
        $('#RemoveHeaderField').parent().hide(); // hide label
        $("#RemoveHeaderField").hide(); // hide checkbox

        }
}).trigger('change');

$("#PostButton").click(function() {
    if ($('#UsecaseField').find(":selected").text() === "fence")
    {
      $("#SamplingRateField").prop('required', true);
    }
    else {
      $("#SamplingRateField").prop('required', false);
    }
});

$(document).ready(function(){
    $("#SpecialDataField").click(function(){
        if($(this).is(":checked")){
          console.log("checked")
            $("#ActField").prop('required',false);
            $("#ProjectField").prop('required',false);
            $("#RegionField").prop('required',false);
        }
        else if($(this).is(":not(:checked)")){
          console.log("not checked")
            $("#ActField").prop('required',true);
            $("#ProjectField").prop('required',true);
            $("#RegionField").prop('required',true);
        }
    });
});


// select all button click handler
// check all checkbox in the form.
$( "#SelectAllButton").click(function() {
   $(".SubsetCb").prop('checked', true);
});

$( "#UncheckButton").click(function() {
   $(".SubsetCb").prop('checked', false);
});

$( "#SelectAllDataButton").click(function() {
  $(this).toggleClass('active');
  if ($(this).hasClass("active"))
    $(".DataSubsetCb").prop('checked', true);
  else
    $(".DataSubsetCb").prop('checked', false);
});
