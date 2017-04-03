(function($) {
	$(function() {
		///////////////////
		//    GLOBALS    //
		///////////////////

		var gameDuration = 60 * 60 * 1000;
		var debug = true;
		var tableTemplate;
		var queueTemplate;
		var tableTypes;


		///////////////////
		//   RETRIEVAL   //
		///////////////////

		function getTables() {
			getTableTypes(function () {
				$.getJSON('/api/tables', function(data) {
					if(!tableTemplate) {
						window.setTimeout(getTables, 500);
						return;
					}
					data["tabletypes"] = jQuery.extend(true, [], window.tableTypes);
					$("#tables").html(Mustache.render(tableTemplate, data));
					$(".tabletype").change(window.tableType);
					$(".table").each(function (i, table) {
						var x = $(table).data("x");
						var y = $(table).data("y");
						if(x !== undefined)
							$(table).css({'left':x})
						if(y !== undefined)
							$(table).css({'top':y})
						var tabletype = $(this).children(".tabletype");
						tabletype.val(tabletype.data("type"));
					});
					$(".table").draggable({
						snap:true,
						snapMode:"both",
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
							else
								refresh();
						}
					}).disableSelection();
				}).fail(window.xhrError);
			});
		}
		function getQueue() {
			$.getJSON('/api/queue', function(data) {
				if(!queueTemplate) {
					window.setTimeout(getQueue, 500);
					return;
				}
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
		window.refresh = function() {
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
		var timeInterval = window.setInterval(updateTimes, 1000 * 10);

		///////////////////
		//    BUTTONS    //
		///////////////////


		window.login = function() {
			var password = $("#password").val();
			$("#password").val("");
			window.api("login", true, {'password':password});
		}
		window.addTable = function() {
			window.api("tables", true);
		};
		window.deleteTable = function(id) {
			window.api("deletetable", true, {'table': id});
		};
		window.startTable = function(table) {
			window.api("starttable", true, {'table': table})
		};
		window.fillTable = function(table) {
			window.api("filltable", true, {'table': table});
		};
		window.notifyTable = function(table) {
			window.api("notifytable", false, {'table': table})
		};
		window.beginnerTable = function(table) {
			window.api("beginnertable", true, {'table': table})
		};
		window.clearTable = function(table) {
			window.api("cleartable", true, {'table': table});
		};
		window.editTable = function(table) {
			var p = $("#table-" + table);
			var n = p.children("span.name");
			if(n.length === 0) {
				n = p.children("input.newname");
				window.api("edittable", true, {'table':table, 'newname':n.val()});
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
			window.api("queue", true, {'name':name, 'phone':phone, 'numplayers':numplayers});
		};
		window.beginnerSignup = function() {
			var name = $("#name").val();
			var phone = $("#phone").val();
			var numplayers = $("#numplayers").val();
			window.api("queue", true, {'name':name, 'phone':phone, 'numplayers':numplayers, 'beginner': true})
		};
		window.deletePlayer = function(player) {
			window.api("deleteplayer", true, {'player':player});
		};
		window.editPlayer = function(player) {
			var p = $("#player-" + player);
			var n = p.children("span.name");
			if(n.length === 0) {
				n = p.children("input.newname");
				window.api("editplayer", true, {'player':player, 'newname':n.val()});
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
			window.api("notifyplayer", true, {'player':player});
		};
		window.tableType = function() {
			var data = {'table': $(this).data("table"), 'type': $(this).val()};
			window.api("tabletype", true, data);
		};
	});
})(jQuery);


