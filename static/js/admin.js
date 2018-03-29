$(function() {
	var tableTypesTemplate, teachingSessionsTemplate;
	$.get("/static/mustache/tabletypes.mst", function(data) {
		tableTypesTemplate = data;
		Mustache.parse(data);
	});
	$.get("/static/mustache/teachingsessions.mst", function(data) {
		teachingSessionsTemplate = data;
		Mustache.parse(data);
	});
	window.refresh = function() {
		console.log("refresh");
		getTableTypes();
		getTeachingSessions();
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
			$("#tabletypes").html(Mustache.render(tableTypesTemplate, data));
		});
	}
	function getTeachingSessions() {
		$.getJSON("/api/teachingsessions", function(data) {
			if(!teachingSessionsTemplate) {
				window.setTimeout(getTeachingSessions, 500);
				return;
			}
			$("#teachingsessionlist").html(Mustache.render(teachingSessionsTemplate, data));
			$("#teachingsessionlist .delete").click(function() {
				var time = $(this).parent(".teachingsession").data('time');
				window.api("deleteteachingsession", false, {'time': time}, function() {
					getTeachingSessions();
				});
			});
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
			if(data.status === "success")
				getAnnouncement();
		}, "json");
	}
	$("#addannouncement").click(addAnnouncement);
	$("#announcement").keyup(function(e)  {
		if(e.keyCode == 13)
			addAnnouncement();
	});

	$("#teachingsessiontime").datetimepicker({'format':'Y-m-d H:i:00'});
	function addSession() {
		var text = $("#teachingsessiontime").val();
		if(text.length == 0) {
			$("#session").notify("Please enter some a time");
			return;
		}
		$.post("/api/teachingsessions", {'time':text}, function(data) {
			$.notify(data.message, data.status);
			if(data.status === "success")
				getTeachingSessions();
		}, "json");
	}
	$("#addsession").click(addSession);
	$("#teachingsessiontime").keyup(function(e)  {
		if(e.keyCode == 13)
			addSession();
	});

	function addTableType() {
		var prefs = {
			"type": $("#type").val(),
			"gameduration": $("#duration").val(),
		 	"numplayers": $("#numplayers").val()
		};
		window.api("addgametype", true, prefs);
		getTableTypes();
	}
	window.deleteTableType = function(table) {
		var data = {"type":table};
		console.log(data);
		window.api("deletetabletype", true, data);
	}
	$("#addgametype").click(addTableType);
});
