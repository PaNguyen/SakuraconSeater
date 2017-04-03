$(function() {
	var tableTypesTemplate;
	$.get("/static/mustache/tabletypes.mst", function(data) {
		tableTypesTemplate = data;
		Mustache.parse(data);
	});
	window.refresh = function() {
		console.log("refresh");
		getTableTypes();
		getAnnouncement();
	}
	function getAnnouncement() {
		$.getJSON("/api/announcement", function(data) {
			$("#announcement").val(data.message);
		});
	}
	function getTableTypes() {
		$.getJSON("/api/tabletype", function(data) {
				if(!tableTypesTemplate) {
					window.setTimeout(getTableTypes, 500);
					return;
				}
				data = {'tabletypes':data};
			console.log(data);
				$("#tabletypes").html(Mustache.render(tableTypesTemplate, data));
		});
	}
	refresh();
	function addAnnouncement() {
		var text = $("#announcement").val();
		if(text.length == 0) {
			$("#announcement").notify("Please enter some announcement text");
			return;
		}
		$.post("/api/announcement", {'announcement':text}, function(data) {
			$.notify(data.message, data.status);
		}, "json");
	}
	$("#addannouncement").click(addAnnouncement);
	$("#announcement").keyup(function(e)  {
		if(e.keyCode == 13)
			addAnnouncement();
	});

	function updatePreferences() {
		var prefs = {
			"gameduration": $("#duration").val(),
		 	"numplayers": $("#numplayers").val()
		};
		$.post("/api/preferences", {'preferences':JSON.stringify(prefs)}, function(data) {
			$.notify(data.message, data.status);
		}, "json");
	}
	function addTableType() {
		var prefs = {
			"type": $("#type").val(),
			"gameduration": $("#duration").val(),
		 	"numplayers": $("#numplayers").val()
		};
		window.api("addgametype", true, prefs);
	}
	window.deleteTableType = function(table) {
		var data = {"type":table};
		console.log(data);
		window.api("deletetabletype", true, data);
	}
	$("#addgametype").click(addTableType);
});
