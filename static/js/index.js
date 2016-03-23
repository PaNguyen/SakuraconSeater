$(function() {
	var queueTemplate;
	function getQueue() {
		$.getJSON('/api/queue', function(data) {
			data.LoggedIn = false;
			$("#queue").html(Mustache.render(queueTemplate, data));
		}).fail(window.xhrError);
	}
	$.get("/static/mustache/queue.mst", function(data) {
		queueTemplate = data;
		Mustache.parse(data);
	});
	window.setInterval(getQueue, 1000);
});
