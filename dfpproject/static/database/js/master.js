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
      $("#RegionField").prop("disabled", false);
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
      $("#ActField").prop("disabled", false);
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
      $("#ActSpeField").prop("disabled", false);
      $("#ActSpeField").html(data);
    }
  });

});


// $(document).ready(function(){
//     $("#SpecialDataField").click(function(){
//         if($(this).is(":checked")){
//             $("#ActField").prop('required',false);
//             $("#ProjectField").prop('required',false);
//             $("#RegionField").prop('required',false);
//         }
//         else if($(this).is(":not(:checked)")){
//             $("#ActField").prop('required',true);
//             $("#ProjectField").prop('required',true);
//             $("#RegionField").prop('required',true);
//         }
//     });
// });
