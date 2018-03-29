$(function() {
	var queueTemplate;
	var sessions;
	var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
	function getQueue() {
		$.getJSON('/api/queue', function(data) {
			if(queueTemplate === undefined) {
				window.setTimeout(getQueue, 500);
				return;
			}
			data.LoggedIn = false;
			$("#queue").html(Mustache.render(queueTemplate, data));
		}).fail(window.xhrError);
	}
	var updateSession;
	updateSession = function() {
		if(sessions === undefined) {
			$.getJSON("/api/teachingsessions", function(data) {
				times = data['times'];
				sessions = [];
				for(var i = 0; i < times.length; ++i) {
					sessions.push(new Date(times[i]['Time'].replace(' ', 'T')));
				}
				updateSession();
			});
		}
		else if(sessions.length > 0) {
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
			$("#nextsession").text("No more teaching presentations");
		}
	}
	function refresh() {
		getQueue();
		updateSession();
	}
	$.get("/static/mustache/queue.mst", function(data) {
		queueTemplate = data;
		Mustache.parse(data);
	});
	refresh();
	window.setInterval(refresh, 1000 * 5);
});
