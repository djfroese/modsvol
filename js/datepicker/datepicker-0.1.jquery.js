// Utility

if (typeof Object.create !== 'function' ) {
    Object.create = function ( obj ) {
        function F() {};
        F.prototype = obj;
        return new F();
    };
}

function timefnum(minutes) {
    hours = Math.floor(minutes / 60);
    minutes = minutes % 60;
    if (minutes < 10) {
        minutes = "0"+minutes;
    }
    
    if (hours < 10) {
        hours = "0"+hours;
    }
    
    return hours + ":" + minutes;
}

function numftime(time) {
    var vals = time.split(':');
    
    hours = parseInt(vals[0]);
    minutes = parseInt(vals[1]);
    return ( hours * 60 ) + minutes
}


( function ( $, window, document, undefined ) {
    var DatePicker = {
        init: function( options, element ) {
            var self = this;
            self.element = element;
            self.$element = $( element );
            
            self.options = $.extend ( {}, $.fn.datepicker.options, options);
            
            self.months = ['January','February','March','April','May','June',
                        'July','August','September','October','November','December'];
            self.days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
            
            self.cycle();
            
            self.element.createdPicker = true;
        },
        
        cycle: function (  ) {
            var self = this;
            
            aval = self.$element.val();
            if ( aval !== "" ) {
                self.currentDate = new Date(self.$element.val().split("T")[0]);
            } else {
                self.currentDate = new Date();
            }
            
            self.build( );
            
            $('body').click(function ( event ) {
                //event.stopPropagation();
                if (event.target == self.picker || event.target == self.element || $(event.target).parents(".datetime-window").size() ) {
                    ;
                } else {
                    self.close();
                }
            });
            
            self.$element.focus(function () {    
                self.display();
            });
            
            self.$element.attr('readonly',true);
            if ( !self.$element.hasClass('datepicker')) {
                self.$element.addClass('datepicker');
            }
        },
        
        build: function (  ) {
            var self = this;
            
            //self.currentDate = date;
            
            var month = self.currentDate.getMonth();
            var year = self.currentDate.getFullYear();
            var firstOfMonth = new Date(year, month, 1, 0, 0, 0, 0);
            
            var done = false;
            var started = false;
            
            
            today = new Date()
            today = new Date(today.getFullYear(),today.getMonth(),today.getDate(),0,0,0,0);
            var startday = firstOfMonth.getDay();
            
            self.picker = $("<div></div>").addClass('datetime-window');
            
            var header = $("<div class='month-title'></div>");
            
            self.prevBtn = $("<button class='prev btn btn-default glyphicon glyphicon-chevron-left'></button>");
            self.nextBtn = $("<button class='prev btn btn-default glyphicon glyphicon-chevron-right'></button>");
            
            self.monthTitle = $("<span></span>");
            self.monthTitle.append("<strong>"+self.months[month] + " " + year + "</strong>");
            
            header.append(self.prevBtn);
            header.append(self.monthTitle);
            header.append(self.nextBtn);
            
            self.picker.append(header);
            
            self.table = $("<div></div");
            
            var month = $("<table></table>").addClass("month");
            
            var thead = $("<thead></thead>");
            var row = $("<tr></tr>");
            
            for (var i = 0; i < self.days.length; i++) {
                row.append($('<td></td>').append(self.days[i].substr(0, self.options.shortWeek)));
            }
            
            thead.append(row);
            month.append(thead);
            
            self.tbody = self.buildMonth(self.currentDate)       
            month.append(self.tbody);
            
            self.table.append(month);
            self.picker.append(month);
            
            self.todayBtn = $("<button class='btn btn-primary'></button>");
            self.todayBtn.append("Today");
            self.todayBtn.addClass('pull-right');
            self.picker.append(self.todayBtn);
            
            self.closeBtn = $("<button class='btn btn-default'></button>");
            self.closeBtn.append('Close');
            self.closeBtn.addClass('pull-left');
            self.picker.append(self.closeBtn);
            
            self.picker.on('click', '.month td', function (event) {
                self.$element.val($(this).attr('value'));
                if ( self.options.time ) {
                    self.$element.val($(self.$element).val()+"T"+self.time);
                }
                self.close();
            });
            
            if (self.options.time) {
                self.time = self.buildTime();
                self.picker.append(self.time);
            }
            
            var zi = self.$element.parents(".dialog-window").css('z-index');
            
            self.picker.css('z-index',zi+10);
            
        },

        buildMonth: function ( ) {
            var self = this;
            
            var month = self.currentDate.getMonth();
            var year = self.currentDate.getFullYear();
            var firstOfMonth = new Date(year, month, 1, 0, 0, 0, 0);
            
            today = new Date()
            today = new Date(today.getFullYear(),today.getMonth(),today.getDate(),0,0,0,0);
            var startday = firstOfMonth.getDay();
            
            var done = false;
            var started = false;
            
            var tbody = $("<tbody class='dates'></tbody>");
            
            firstOfMonth = new Date(firstOfMonth.getFullYear(),firstOfMonth.getMonth(),firstOfMonth.getDate()-firstOfMonth.getDay(),0,0,0,0);
            
            for (var i = 0; i < 9 && !done; i++) {
                row = $("<tr></tr>");
                for (var j = 0; j < 7; j++) {
                    cell = $("<td></td>");
                    //if (started) {
                        
                    if (today.getTime() == firstOfMonth.getTime()) {
                        cell.addClass('today');
                    }
                    
                    if (firstOfMonth.getMonth() != self.currentDate.getMonth()) {
                        cell.addClass('eitherside');
                    }
                    
                    cell.attr('value',firstOfMonth.getFullYear() + "-" + (firstOfMonth.getMonth()+1) + "-" + firstOfMonth.getDate());
                    cell.append(firstOfMonth.getDate());
                    firstOfMonth.setDate(firstOfMonth.getDate()+1);
                    
                    if ( firstOfMonth.getMonth() > self.currentDate.getMonth() || 
                            (firstOfMonth.getMonth() == 0 && self.currentDate.getMonth() == 11) ) {
                        if (!(firstOfMonth.getMonth() == 11 && self.currentDate.getMonth() == 0 )) {
                            done = true;
                        }
                    }
                    row.append(cell);
                }
                tbody.append(row);
                if (done) {
                    break;
                }
            }
            
            return tbody;
        },
        
        buildTime: function() {
            var self = this;
            
            var hours = self.currentDate.getHours();
            var minutes = self.currentDate.getMinutes();
            
            console.log(hours);
            console.log(minutes);
            
            var timedisplay = $("<div class='ui-time'></div>");
            
            var timeslider = $("<input type='range' min=0 max=1440 step=15 value=0 />");
            var timeview = $("<input type='text' value='00:00' />");
            
            timeslider.change(function () {
                timeview.val(timefnum($(this).val()));
                self.$element.val(self.$element.val().split("T")[0]+"T"+timefnum($(timeslider).val()));
                self.time = $(timeview).val();
            });
            
            timedisplay.append(timeslider);
            timedisplay.append(timeview);
            
            timedisplay.addClass('ui-time');
            
            console.log(timedisplay);
            
            //self.picker.append(timedisplay);
            
            return timedisplay;
            
        },
        
        display: function () {
            var self = this;
            
            $('body').append(self.picker);            
            
            self.nextBtn.click(function(event) {
                self.currentDate = new Date(self.currentDate.getFullYear(), self.currentDate.getMonth()+1,2,0,0,0,0);
                self.picker.remove();
                self.build();
                self.display();
            });
            
            self.prevBtn.click(function( event ) {
                self.currentDate = new Date(self.currentDate.getFullYear(), self.currentDate.getMonth()-1,2,0,0,0,0);
                self.picker.remove();
                self.build();
                self.display();
            });
            
            self.todayBtn.click(function () {
                self.currentDate = new Date();
                self.picker.remove();
                self.build()
                self.display();
            });
            
            self.closeBtn.click(function () {
                self.close();
            });
            
            self.picker.show();
            
            var offset = self.$element.offset();
            offset.top = offset.top + self.$element.height() + 16;
            offset.left = offset.left;
            self.picker.offset(offset);
        },
        
        close: function () {
            var self = this;
            
            self.picker.hide();
        }
    };
    
    
    $.fn.datepicker = function( options ) {
		return this.each(function() {
		    if ( !this.datepicker ) {
		        var datepicker = Object.create( DatePicker );
		        datepicker.init( options, this );
		        this.datepicker = datepicker;
		    }
			//$.data( this, 'datepicker', datepicker );
		});
	};
    
    $.fn.datepicker.options = {
        width: 'auto',
        height: 'auto',
        shortWeek: 3,
        time: false
        
    };
    
}( jQuery, window, document ));