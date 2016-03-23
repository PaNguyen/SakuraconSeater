function timeString(time) {
	time = Math.floor(time / 1000);
	var seconds = time % 60;
	time = Math.floor(time / 60);
	var minutes = time % 60;
	var hours = Math.floor(time / 60);
	return (0 + hours.toString()).slice(-2) + ":" + (0 + minutes.toString()).slice(-2) + ":" + (0 + seconds.toString()).slice(-2);
}

window.xhrError = function(xhr, status, error) {
	console.log(status + ": " + error);
	console.log(xhr);
};
