$(function() {
	function getAnnouncement() {
		$.getJSON('/api/announcement', function(data) {
			$("#announcement").text(data.message);
		}).fail(window.xhrError);
	}
	window.setInterval(getAnnouncement, 1000);
});
