(function($) {
	$(function() {
		///////////////////
		//    GLOBALS    //
		///////////////////

		var gameDuration = 60 * 60 * 1000;
		var debug = true;
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
		function updateTableTimes() {
		}
		function getTables(callback) {
			$.getJSON('/api/tables', function(data) {
				window.tables = data;
				data.LoggedIn = window.loggedIn;
				$("#tables").html(Mustache.render(tableTemplate, data));
				$(".table.playing").each(function(i, elem) {
					$(elem).data("started-date", new Date($(elem).data("started")));
				})
				if(window.loggedIn)
					$(".players").sortable({
						connectWith:"#playerqueue, .players",
						update:function(event, ui) {
							// if we're moving a queue player back to a table
							if(this === ui.item.parent()[0] && ui.sender !== null) {
								$.post("/api/tableplayer",
								       {'player':ui.item.data("id"),
									       'table':ui.item.parents(".table").data("id")},
								       function(data) {
									       notify(data.message, data.status);
									       if(data.status === "error") {
										       $(this).sortable("cancel");
										       ui.sender.sortable("cancel");
									       }
								}.bind(this), 'json');
							}
						}
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
				if(window.loggedIn)
					$("#playerqueue").sortable({
						connectWith:".players",
						update:function(event, ui) {
							// if we're moving a table player back to the queue
							if(this === ui.item.parent()[0] && ui.sender !== null) {
								$.post("/api/queueplayer",
								       {'player':ui.item.data("id")},
								       function(data) {
									       notify(data.message, data.status);

									       if(data.status === "error") {
										       $(this).sortable("cancel");
										       ui.sender.sortable("cancel");
									       }
								}.bind(this), 'json');
							}
						}
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
		window.setInterval(function () {
			var now = new Date();
			$(".table.playing").each(function(i, table) {
				var started = $(table).data("started-date");
				var elapsed = Math.floor((now - started));
				$(table).children(".duration").text(timeString(elapsed));
				if(elapsed > gameDuration)
					$(table).addClass("warn");
			});
		}, 1000);

		///////////////////
		//    BUTTONS    //
		///////////////////

		$("#login").click(function() {
			var password = $("#password").val();
			$("#password").val("");
			$.post("/api/login", {'password':password}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, 'json');
		});
		window.addTable = function() {
			$.post("/api/tables", function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					getTables();
			}, "json");
		};
		window.deleteTable = function(id) {
			$.post("/api/deletetable", {'table': id}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					getTables();
			}, "json");
		};
		window.startTable = function(table) {
			$.post("/api/starttable", {'table': table}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success") {
					getTables();
				}
			}, "json");
		};
		window.clearTable = function(table) {
			$.post("/api/cleartable", {'table': table}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success") {
					getTables();
				}
			}, "json");
		};
		window.signup = function() {
			var name = $("#name").val();
			var phone = $("#phone").val();
			$.post("/api/queue", {'name':name, 'phone':phone}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")  {
					$("#name").val("");
					$("#phone").val("");
					getQueue();
				}
			}, "json");
		};
		window.deletePlayer = function(player) {
			$.post("/api/deleteplayer", {'player':player}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")  {
					getQueue();
					getTables();
				}
			}, "json");
		};
		window.notifyPlayer = function(player) {
			$.post("/api/notifyPlayer", {'player':player}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")  {
					getQueue();
					getTables();
				}
			}, "json");
		};




		///////////////////
		//    UTILITY    //
		///////////////////

		function timeString(time) {
			time = Math.floor(time / 1000);
			var seconds = time % 60;
			time = Math.floor(time / 60);
			var minutes = time % 60;
			var hours = Math.floor(time / 60);
			return (0 + hours.toString()).slice(-2) + ":" + (0 + minutes.toString()).slice(-2) + ":" + (0 + seconds.toString()).slice(-2);
		}

		function notify(message, status) {
			if(status === "error" || debug)
				$.notify(message, status);
		}

		window.xhrError = function(xhr, status, error) {
			console.log(status + ": " + error);
			console.log(xhr);
		};

	});
})(jQuery);

