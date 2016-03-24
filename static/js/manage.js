(function($) {
	$(function() {
		///////////////////
		//    GLOBALS    //
		///////////////////

		var gameDuration = 60 * 60 * 1000;
		var debug = true;
		var tableTemplate;
		var queueTemplate;


		///////////////////
		//   RETRIEVAL   //
		///////////////////

		function getTables(callback) {
			$.getJSON('/api/tables', function(data) {
				window.tables = data;
				$("#tables").html(Mustache.render(tableTemplate, data));
				$(".table").draggable({
					snap:true,
					stop:function(event, ui) {
						$.post("/api/tableposition",
						       {'x':ui.position.left,
							       'y':ui.position.top,
							       'table':ui.helper.data("id")},
						       function(data) {
							       notify(data.message, data.status);
						}, 'json');
					}
				});
				$(".table").each(function (i, table) {
					var x = $(table).data("x");
					var y = $(table).data("y");
					if(x !== undefined && y !== undefined)
						$(table).css({'top':y,'left':x})
				});
				$(".players").sortable({
					connectWith:"#playerqueue, .players, #beginnerqueue",
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
									       return;
								       }
								       refresh();
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
				data.LoggedIn = true;
				$("#queue").html(Mustache.render(queueTemplate, data));
				$("#playerqueue").sortable({
					connectWith:".players,#beginnerqueue",
					update:function(event, ui) {
						// if we're moving a table player back to the queue
						if(this === ui.item.parent()[0] && ui.sender !== null) {
							$.post("/api/queueplayer",
							       {'player':ui.item.data("id")},
							       function(data) {
								       notify(data.message, data.status);
								       refresh();

								       if(data.status === "error") {
									       $(this).sortable("cancel");
									       ui.sender.sortable("cancel");
								       }
							}.bind(this), 'json');
						}
						else
							refresh();
					}
				}).disableSelection();
				$("#beginnerqueue").sortable({
					connectWith:".players, #playerqueue",
					update:function(event, ui) {
						// if we're moving a table player back to the queue
						if(this === ui.item.parent()[0] && ui.sender !== null) {
							$.post("/api/beginnerqueueplayer",
							       {'player':ui.item.data("id")},
							       function(data) {
								       notify(data.message, data.status);
								       refresh();

								       if(data.status === "error") {
									       $(this).sortable("cancel");
									       ui.sender.sortable("cancel");
								       }
							}.bind(this), 'json');
						}
						else
							refresh();
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
			getTables();
			getQueue();
		}
		refresh();
		function updateTimes() {
			var now = new Date();
			$(".table.playing").each(function(i, table) {
				var started = $(table).data("started-date");
				if(started === undefined) {
					$(table).data("started-date", new Date($(table).data("started")));
					started = $(table).data("started-date");
				}
				var elapsed = Math.floor(now - started);
				$(table).children(".duration").text(timeString(elapsed));
				if(elapsed > gameDuration)
					$(table).addClass("warn");
			});
			$(".player.queued, #queueeta, #beginnereta").each(function(i, player) {
				var eta = $(player).data("eta-date");
				if(eta === undefined) {
					$(player).data("eta-date", new Date($(player).data("eta")));
					eta = $(player).data("eta-date");
				}
				var remaining = Math.floor(eta - now);
				if(remaining > 0)
					$(player).children(".remaining").text(timeString(remaining));
				else
					$(player).children(".remaining").text("NOW");
			});
		}
		var timeInterval = window.setInterval(updateTimes, 1000);

		///////////////////
		//    BUTTONS    //
		///////////////////


		function login() {
			var password = $("#password").val();
			$("#password").val("");
			$.post("/api/login", {'password':password}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, 'json');
		}
		window.api = function(name, toRefresh, data) {
			$.post("/api/" + name, data, function(data) {
				notify(data.message, data.status);
				if(toRefresh && data.status === "success")
					refresh();
			}, "json");
		}
		window.addTable = function() {
			$.post("/api/tables", function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.deleteTable = function(id) {
			$.post("/api/deletetable", {'table': id}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.startTable = function(table) {
			$.post("/api/starttable", {'table': table}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.fillTable = function(table) {
			$.post("/api/filltable", {'table': table}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.notifyTable = function(table) {
			$.post("/api/notifytable", {'table': table}, function(data) {
				notify(data.message, data.status);
			}, "json");
		};
		window.beginnerTable = function(table) {
			$.post("/api/beginnertable", {'table': table}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.clearTable = function(table) {
			$.post("/api/cleartable", {'table': table}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.editTable = function(table) {
			var p = $("#table-" + table);
			var n = p.children("span.name");
			if(n.length === 0) {
				n = p.children("input.newname");
				$.post("/api/edittable", {'table':table, 'newname':n.val()}, function(data) {
					notify(data.message, data.status);
					if(data.status === "success")
						refresh();
				}, "json");
			}
			else {
				n.replaceWith($("<input id='table-" + table + "' type='text' class='newname' value='" + n.text() + "'></input>"));
				$("#table-" + table).keyup(function(e) {
					if(e.keyCode == 13)
						window.editTable(table);
				});
				$("#table-" + table).focus();
			}
		};
		window.signup = function() {
			var name = $("#name").val();
			var phone = $("#phone").val();
			var numplayers = $("#numplayers").val();
			$.post("/api/queue", {'name':name, 'phone':phone, 'numplayers':numplayers}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.beginnerSignup = function() {
			var name = $("#name").val();
			var phone = $("#phone").val();
			var numplayers = $("#numplayers").val();
			$.post("/api/queue", {'name':name, 'phone':phone, 'numplayers':numplayers, 'beginner': true}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.deletePlayer = function(player) {
			$.post("/api/deleteplayer", {'player':player}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};
		window.editPlayer = function(player) {
			var p = $("#player-" + player);
			var n = p.children("span.name");
			if(n.length === 0) {
				n = p.children("input.newname");
				$.post("/api/editplayer", {'player':player, 'newname':n.val()}, function(data) {
					notify(data.message, data.status);
					if(data.status === "success")
						refresh();
				}, "json");
			}
			else {
				n.replaceWith($("<input id='player-" + player + "' type='text' class='newname' value='" + n.text() + "'></input>"));
				$("#player-" + player).keyup(function(e) {
					if(e.keyCode == 13)
						window.editPlayer(player);
				}).focus();
			}
		};
		window.notifyPlayer = function(player) {
			$.post("/api/notifyplayer", {'player':player}, function(data) {
				notify(data.message, data.status);
				if(data.status === "success")
					refresh();
			}, "json");
		};


		///////////////////
		//    UTILITY    //
		///////////////////

		function notify(message, status) {
			if(status === "error" || debug)
				$.notify(message, status);
		}
	});
})(jQuery);

