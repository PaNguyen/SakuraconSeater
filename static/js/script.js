(function($) {
	$(function() {
		///////////////////
		//    GLOBALS    //
		///////////////////

		window.loggedIn = false;
		var tableTemplate;
		var queueTemplate;


		///////////////////
		//   RETRIEVAL   //
		///////////////////

		function getLoggedIn(callback) {
			$.getJSON('/api/login', function(data) {
				window.loggedIn = data.loggedIn;
				if(window.loggedIn)
					$("#loginform").hide(1000);

				if(typeof callback === "function")
					callback();
			}).fail(window.xhrError);
		}
		function getTables(callback) {
			$.getJSON('/api/tables', function(data) {
				window.tables = data;
				data.LoggedIn = window.loggedIn;
				$("#tables").html(Mustache.render(tableTemplate, data));
				$(".players").sortable({
					connectWith:"#playerqueue"
				}).disableSelection();

				if(typeof callback === "function")
					callback();
			}).fail(window.xhrError);
		}
		function getQueue(callback) {
			$.getJSON('/api/queue', function(data) {
				window.tables = data;
				data.LoggedIn = window.loggedIn;
				$("#queue").html(Mustache.render(queueTemplate, data));
				$("#playerqueue").sortable({
					connectWith:".players"
				}).disableSelection();

				if(typeof callback === "function")
					callback();
			}).fail(window.xhrError);
		}

		///////////////////
		//     SETUP     //
		///////////////////

		$.get("/static/mustache/table.mst", function(data) {
			tableTemplate = data;
			Mustache.parse(data);
		});
		$.get("/static/mustache/queue.mst", function(data) {
			queueTemplate = data;
			Mustache.parse(data);
		});
		function refresh() {
			getLoggedIn(function() {
				getTables();
				getQueue();
			});
		}
		refresh();

		///////////////////
		//    BUTTONS    //
		///////////////////

		$("#login").click(function() {
			var password = $("#password").val();
			$("#password").val("");
			$.post("/api/login", {'password':password}, function(data) {
				$.notify(data.message, data.status);
				refresh();
			}, 'json');
		});
		window.addTable = function() {
			$.post("/api/tables", function(data) {
				$.notify(data.message, data.status);
				if(data.status === "success")
					getTables();
			}, "json");
		};
		window.startButton = function(table) {
			console.log(table);
		};
		window.signup = function() {
			var name = $("#name").val();
			var phone = $("#phone").val();
			$.post("/api/queue", {'name':name, 'phone':phone}, function(data) {
				$.notify(data.message, data.status);
				if(data.status === "success")  {
					$("#name").val("");
					$("#phone").val("");
					getQueue();
				}
			}, "json");
		};
		window.deletePlayer = function(player) {
			$.post("/api/deleteplayer", {'player':player}, function(data) {
				$.notify(data.message, data.status);
				if(data.status === "success")  {
					getQueue();
					getTables();
				}
			}, "json");
		};
		window.notifyPlayer = function(player) {
			$.post("/api/notifyPlayer", {'player':player}, function(data) {
				$.notify(data.message, data.status);
				if(data.status === "success")  {
					getQueue();
					getTables();
				}
			}, "json");
		};




		window.xhrError = function(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		};

	});
})(jQuery);

