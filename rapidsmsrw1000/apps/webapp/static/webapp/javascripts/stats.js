/*  TODO: onSelect for date pickers.    */
$(function()
{
    //$('#pickstartdate').datepick({dateFormat:'dd.mm.yyyy'});
    //$('#pickenddate').datepick({dateFormat:'dd.mm.yyyy'});
	
    $('#navlocation').change(function(evt)
    {	
	var loc = $(this).attr('value').split('.')[1];
	if ( loc == 'HealthCentre') loc = "Location";
        if ($(this).attr('value') != ''){window.location = (window.location.pathname + '?'+loc.toLowerCase()+'=' +
        $(this).attr('value').split('.')[0] + '&start_date=' +
        $('#pickstartdate').attr('value') + '&end_date=' + $('#pickenddate').attr('value'));
	} else {
			window.location = window.location.pathname;			
			}
    });
    

    $('#provchoose').change(function(evt)
    {	
	var group = "?";
	if ($('#group')) group = '?group=' + $('#group').attr('value'); 
	
        if ($(this).attr('value') != ''){window.location = window.location.pathname + group + '&province=' +
        $(this).attr('value') + '&start_date=' +  $('#pickstartdate').attr('value') + '&end_date=' + $('#pickenddate').attr('value');
	} else {
			window.location = window.location.pathname + group + '&start_date=' + $('#pickstartdate').attr('value') + '&end_date=' +
        $('#pickenddate').attr('value');			
			}
	
    });

    condDisableDistricts();
    $('#distchoose').change(function()
    {
	var group = "?";
	if ($('#group')) group = '?group=' + $('#group').attr('value');

        if ($(this).attr('value') != ''){ window.location = (window.location.pathname + group + '&district=' +
        $(this).attr('value') + '&province=' + $('#provchoose').attr('value')
        + '&start_date=' + $('#pickstartdate').attr('value') + '&end_date=' +
        $('#pickenddate').attr('value'));
	}
		else {
			window.location = (window.location.pathname + group + '&province=' + $('#provchoose').attr('value')
        + '&start_date=' + $('#pickstartdate').attr('value') + '&end_date=' +
        $('#pickenddate').attr('value'));			
			}
    });

    condDisableLocations();
    $('#locchoose').change(function()
    {
       var group = "?";
       if ($('#group')) group = '?group=' + $('#group').attr('value');
       if ($(this).attr('value') != '') { window.location = (window.location.pathname + group + '&location=' +
        $(this).attr('value') + '&province=' + $('#provchoose').attr('value') +
        '&district=' + $('#distchoose').attr('value') + '&start_date=' +
        $('#pickstartdate').attr('value') + '&end_date=' + $('#pickenddate').attr('value'));
	} 
		else{
			window.location = (window.location.pathname + group + '&province=' + $('#provchoose').attr('value') +
        '&district=' + $('#distchoose').attr('value') + '&start_date=' +
        $('#pickstartdate').attr('value') + '&end_date=' + $('#pickenddate').attr('value'));
			}
    });
});

function condDisableDistricts()
{
    var loc = window.location.toString();
    if(loc.search(/province/) != -1) return;
    $('#distchoose').hide();
}

function condDisableLocations()
{
    var loc = window.location.toString();
    if(loc.search(/district/) != -1) return;
    $('#locchoose').hide();
}
