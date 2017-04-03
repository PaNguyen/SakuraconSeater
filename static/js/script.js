function timeString(time) {
	time = Math.floor(time / 1000);
	time = Math.floor(time / 60);
	var minutes = time % 60;
	var hours = Math.floor(time / 60);
	return (0 + hours.toString()).slice(-2) + ":" + (0 + minutes.toString()).slice(-2);
}

window.xhrError = function(xhr, status, error) {
	console.log(status + ": " + error);
	console.log(xhr);
};

function notify(message, status) {
	if(status === "error" || window.debug)
		$.notify(message, status);
}

window.api = function(name, toRefresh, data) {
	$.post("/api/" + name, data, function(data) {
		$.notify(data.message, data.status);
		if(toRefresh && data.status === "success")
			window.refresh();
	}, "json");
}

function getTableTypes(callback) {
	$.getJSON("/api/tabletype", function(data) {
		window.tableTypes = data;
		if(typeof callback === "function")
			callback();
	});
}
