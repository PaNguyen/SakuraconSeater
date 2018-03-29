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

window.api = function(name, toRefresh, data, callback) {
	$.post("/api/" + name, data, function(data) {
		$.notify(data.message, data.status);
		if(data.status === "success") {
			if(toRefresh)
				window.refresh();
			if(typeof callback === 'function')
				callback(data);
		}
	}, "json");
}

function getTableTypes(callback) {
	if(window.tableTypes === undefined)
		$.getJSON("/api/tabletype", function(data) {
			window.tableTypes = data;
			if(typeof callback === "function")
				callback(window.tableTypes);
		});
	else if(typeof callback === "function")
		callback(window.tableTypes);
}
