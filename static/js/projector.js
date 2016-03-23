$(function() {
	var queueTemplate;
	var sessions = [
		new Date("2016-03-25T19:00:00.000Z"),
		new Date("2016-03-26T02:00:00.000Z"),
		new Date("2016-03-26T18:00:00.000Z"),
		new Date("2016-03-27T00:00:00.000Z")
	];
	var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
	function getQueue() {
		$.getJSON('/api/queue', function(data) {
			data.LoggedIn = false;
			$("#queue").html(Mustache.render(queueTemplate, data));
		}).fail(window.xhrError);
	}
	function updateSession() {
		for(var i = 0; i < sessions.length; ++i) {
			var session = sessions[i];
			var now = new Date();
			var delta = session - now;
			if(delta < 0 && delta > -60 * 60 * 1000) {
				var text = "Teaching session in progress.";
				if(i + 1 < sessions.length) {
					session = sessions[i + 1];
					delta = session - now;
					text += " Next teaching session in " + timeString(delta) + " on " + days[session.getDay()] + " at " + session.toTimeString().split(" ")[0];
				}
				else
					text +=  " This is the last session";
				$("#nextsession").text(text);
				return;
			}
			else if(delta > 0) {
				$("#nextsession").text("Next teaching session in " + timeString(delta) + " on " + days[session.getDay()] + " at " + session.toTimeString().split(" ")[0]);
				return;
			}
		}
		$("#nextsession").text("No more teaching sessions");
	}
	function refresh() {
		getQueue();
		updateSession();
	}
	$.get("/static/mustache/queue.mst", function(data) {
		queueTemplate = data;
		Mustache.parse(data);
	});
	window.setInterval(refresh, 1000);
});
