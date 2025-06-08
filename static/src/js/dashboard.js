/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { Domain } from "@web/core/domain";
import { sprintf } from "@web/core/utils/strings";
import { rpc } from "@web/core/network/rpc";


const { Component, useSubEnv, useState, onMounted, onWillStart, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets"

class RoomDashboard extends Component {
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");

    this.state = useState({
      start_date: "",
      end_date: "",
      rooms_status: false,
      hotelStats: {
        'active_booking_count': 0,
        'hall_count': 0,
        'today_check_in': 0,
        'today_check_out': 0,
        'food_count': 0,
        'transports_count': 0,
      },
    });

    useSubEnv({
      config: {
        ...getDefaultConfig(),
        ...this.env.config,
      },
    });
    this.bookingStatus = useRef('bookingStatus');
    this.topCustomer = useRef('topCustomer');
    this.roomType = useRef('roomType');
    this.monthBooking = useRef('monthBooking');
    this.dayBooking = useRef('dayBooking');
    onWillStart(async () => {
      this.state.rooms_status = await rpc("/get/rooms/status");
      let hotelData = await this.orm.call('hotel.booking', 'get_hotel_stats', []);
      if (hotelData) {
        this.state.hotelStats = hotelData;
        this.state.bookingStatusRec = {
          'status': hotelData['room'][0],
          'count': hotelData['room'][1],
        };
        this.state.topCustomerRec = {
          'partner': hotelData['top_customer'][0],
          'amount': hotelData['top_customer'][1],
        };
        this.state.roomTypeRec = {
          'stage': hotelData['get_cat_room'][0],
          'count': hotelData['get_cat_room'][1],
        };
        this.state.monthBookingRec = {
          'month': hotelData['booking_month'][0],
          'count': hotelData['booking_month'][1],
        };
        this.state.dayBookingRec = {
          'day': hotelData['booking_day'][0],
          'confirm_count': hotelData['booking_day'][1],
          'check_in_count': hotelData['booking_day'][2],
          'check_out_count': hotelData['booking_day'][3],
          'cancel_count': hotelData['booking_day'][4],
        };
      }
    });
    onMounted(() => {
      this.renderBookingStatus(this.bookingStatus.el, this.state.bookingStatusRec);
      this.renderTopCustomer(this.topCustomer.el, this.state.topCustomerRec);
      this.renderMonthBooking();
      this.renderDayBooking();
    })
  }

  async filterRooms() {
    const start_date = this.state.start_date;
    const end_date = this.state.end_date;

    if (start_date && end_date) {
      const result = await rpc("/get/rooms/status/by/date", {
        start_date: start_date,
        end_date: end_date,
      });
      if (result) {
        this.state.rooms_status = result;
      }
    }

  }

  dateValidation() {
    let dateOne = document.getElementById('filter_search').value;
    let dateTwo = document.getElementById('filter_search_end').value;

    // Create Date objects from the input values
    let checkInDate = new Date(dateOne);
    let checkOutDate = new Date(dateTwo);

    // Get the alert message element
    let alertMessage = document.getElementById('alert_message');

    // Check if both dates are valid
    if (checkInDate && checkOutDate) {
        // Check if the check-out date is earlier than the check-in date
        if (checkOutDate < checkInDate) {
            alertMessage.textContent = 'It is not possible for the check-out date to exceed the check-in date.';
            alertMessage.classList.add('alert-warning');
        } else {
            // Clear the alert message if dates are valid
            alertMessage.textContent = '';
            alertMessage.classList.remove('alert-warning');
        }
    }
  }



  viewAllBookings() {
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: "Hotel Room Booking",
      target: 'new',
      res_model: 'hotel.booking',
      views: [[false, 'list'], [false, 'form']],
      context: { 'create': false },
    });
  }

  async createRoomBooking() {
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: "Hotel Room Booking",
      target: 'new',
      res_model: 'hotel.booking',
      views: [[false, 'form']],
    });
    this.state.rooms_status = await rpc("/get/rooms/status");
  }

  viewBooking(ev) {
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: "Hotel Room Booking",
      target: 'new',
      res_id: parseInt(ev.target.id),
      res_model: 'hotel.room.details',
      views: [[false, 'form']],
    });
  }

  viewDashboardStatic(type) {
    let model, domain, name;
    let today = new Date();
    let start = new Date(today);
    let end = new Date(today.setDate(today.getDate() + 1));
    start.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);
    if (type === 'active_room') {
      model = 'hotel.booking'
      domain = ['|', ['stages', '=', 'Confirm'], ['stages', '=', 'check_in']]
      name = 'Active Room Booking'
    } else if (type == 'active_hall') {
      model = 'hotel.feast'
      domain = [['stages', '=', 'Confirm']]
      name = 'Active Hall Booking'
    } else if (type == 'today_check_in') {
      model = 'hotel.room.details'
      domain = [['check_in', '>=', start], ['check_in', '<', end], ['stages', '=', 'Booked']]
      name = 'Today Check-in'
    } else if (type == 'today_check_out') {
      model = 'hotel.room.details'
      domain = [['check_out', '>=', start], ['check_out', '<', end], ['stages', '=', 'Booked']]
      name = 'Today Check-out'
    } else if (type == 'food') {
      model = 'hotel.restaurant'
      domain = [['stages', '=', 'Confirm']]
      name = 'Food'
    } else if (type == 'transport') {
      model = 'hotel.transport'
      domain = [['stage', '=', 'pending']]
      name = 'Transport'
    }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: name,
      res_model: model,
      view_mode: 'list',
      views: [[false, 'list'], [false, 'form']],
      target: 'current',
      context: { 'create': false },
      domain: domain,
    });
  }

  renderBookingStatus(div, sessionData) {
    const root = am5.Root.new(div);
    root.setThemes([
      am5themes_Animated.new(root)
    ]);

    const chart = root.container.children.push(am5xy.XYChart.new(root, {
      panX: true,
      panY: true,
      wheelX: "panX",
      wheelY: "zoomX",
      pinchZoomX: true,
      paddingLeft: 0,
      paddingRight: 1
    }));

    const cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
    cursor.lineY.set("visible", false);

    const xRenderer = am5xy.AxisRendererX.new(root, {
      minGridDistance: 20,
      minorGridEnabled: true
    });

    xRenderer.labels.template.setAll({
      rotation: 0,
      centerY: am5.p50,
      centerX: am5.p50,
    });

    xRenderer.grid.template.setAll({
      location: 1
    })

    let xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
      maxDeviation: 0.3,
      categoryField: "country",
      renderer: xRenderer,
      tooltip: am5.Tooltip.new(root, {})
    }));

    const yRenderer = am5xy.AxisRendererY.new(root, {
      strokeOpacity: 0.1
    })

    let yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
      maxDeviation: 0.3,
      renderer: yRenderer
    }));

    let series = chart.series.push(am5xy.ColumnSeries.new(root, {
      name: "Series 1",
      xAxis: xAxis,
      yAxis: yAxis,
      valueYField: "value",
      sequencedInterpolation: true,
      categoryXField: "country",
      tooltip: am5.Tooltip.new(root, {
        labelText: "{valueY}"
      })
    }));

    series.columns.template.setAll({ cornerRadiusTL: 5, cornerRadiusTR: 5, strokeOpacity: 0 });
    series.columns.template.adapters.add("fill", function (fill, target) {
      return chart.get("colors").getIndex(series.columns.indexOf(target));
    });

    series.columns.template.adapters.add("stroke", function (stroke, target) {
      return chart.get("colors").getIndex(series.columns.indexOf(target));
    });

    let data = [];
    for (let i = 0; i < sessionData['status'].length; i++) {

      data.push({
        value: sessionData['count'][i],
        country: sessionData['status'][i],
      })
    }

    xAxis.data.setAll(data);
    series.data.setAll(data);

    series.appear(1000);
    chart.appear(1000, 100);
  }

  renderTopCustomer(div, sessionData) {
    const root = am5.Root.new(div);

    root.setThemes([
      am5themes_Animated.new(root)
    ]);

    const chart = root.container.children.push(am5percent.PieChart.new(root, {
      layout: root.verticalLayout
    }));

    let series = chart.series.push(am5percent.PieSeries.new(root, {
      alignLabels: true,
      calculateAggregates: true,
      valueField: "value",
      categoryField: "category"
    }));

    series.slices.template.setAll({
      strokeWidth: 3,
      stroke: am5.color(0xffffff)
    });

    series.labelsContainer.set("paddingTop", 30)

    series.slices.template.adapters.add("radius", function (radius, target) {
      let dataItem = target.dataItem;
      let high = series.getPrivate("valueHigh");

      if (dataItem) {
        let value = target.dataItem.get("valueWorking", 0);
        return radius * value / high
      }
      return radius;
    });

    series.get("colors").set("colors", [
      am5.color("#f29494"),
      am5.color("#c6ace3"),
      am5.color("#f5c6a2"),
      am5.color("#8bc9c6"),
      am5.color("#d9d9b2")
    ]);

    let chartData = []
    for (let i = 0; i < sessionData['partner'].length; i++) {
      chartData.push({
        value: sessionData['amount'][i],
        category: sessionData['partner'][i],
      })
    }
    series.data.setAll(chartData);

    series.slices.template.set("tooltipText", "{category}: {value}");

    const legend = chart.children.push(am5.Legend.new(root, {
      centerX: am5.p50,
      x: am5.p50,
      marginTop: 15,
      marginBottom: 15
    }));

    legend.data.setAll(series.dataItems);

    series.appear(1000, 100);
  }

  renderMonthBooking() {
    const options = {
      series: [{
        name: 'Booking',
        data: this.state.monthBookingRec['count']
      }],
      chart: {
        height: 350,
      },
      xaxis: {
        categories: this.state.monthBookingRec['month'],
      },
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'dark',
          gradientToColors: ['#FDD835'],
          shadeIntensity: 1,
          type: 'horizontal',
          opacityFrom: 1,
          opacityTo: 1,
          stops: [0, 100, 100, 100]
        },
      }
    };
    this.renderGraph(this.monthBooking.el, options);
  }

  renderDayBooking() {
    var options = {
      series: [{
        name: 'Confirmed Bookings',
        data: this.state.dayBookingRec['confirm_count']
      }, {
        name: 'Checked In Bookings',
        data: this.state.dayBookingRec['check_in_count']
      }, {
        name: 'Checked Out Bookings',
        data: this.state.dayBookingRec['check_out_count']
      }, {
        name: 'Cancelled Bookings',
        data: this.state.dayBookingRec['cancel_count']
      }],
      chart: {
        type: 'bar',
        height: 350,
        stacked: true,
        toolbar: {
          show: true
        },
        zoom: {
          enabled: true
        }
      }, colors: ['#DE63A2', '#64B1FA', '#10A19D', '#98BE55'],
      responsive: [{
        breakpoint: 480,
        options: {
          legend: {
            position: 'bottom',
            offsetX: -10,
            offsetY: 0
          }
        }
      }],
      plotOptions: {
        bar: {
          horizontal: false,
          borderRadius: 10,
          dataLabels: {
            total: {
              enabled: true,
              style: {
                fontSize: '13px',
                fontWeight: 900,
              }
            }
          }
        },
      },
      dataLabels: {
        style: {
          fontSize: '12px',
          fontFamily: 'Helvetica, Arial, sans-serif',
          fontWeight: 'normal',
          colors: ['#292828']
        },
      },
      xaxis: {
        //        type: 'datetime',
        categories: this.state.dayBookingRec['day'],

      },
      legend: {
        position: 'bottom',
        offsetY: 10
      },
      fill: {
        opacity: 1
      }
    };
    this.renderGraph(this.dayBooking.el, options);
  }

  renderGraph(el, options) {
    const graphData = new ApexCharts(el, options);
    graphData.render();
  }
}





//class HotelDashboard extends Component {
//  setup() {
//    this.rpc = useService("rpc");
//    this.action = useService("action");
//    this.orm = useService("orm");
//
//    this.state = useState({
//      hotelStats: {
//        'active_booking_count': 0,
//        'hall_count': 0,
//        'today_check_in': 0,
//        'today_check_out': 0,
//        'food_count': 0,
//        'transports_count': 0,
//      },
//    });
//    useSubEnv({
//      config: {
//        ...getDefaultConfig(),
//        ...this.env.config,
//      },
//    });
//    this.bookingStatus = useRef('bookingStatus');
//    this.topCustomer = useRef('topCustomer');
//    this.roomType = useRef('roomType');
//    this.monthBooking = useRef('monthBooking');
//    this.dayBooking = useRef('dayBooking');
//    onWillStart(async () => {
//      let hotelData = await this.orm.call('hotel.booking', 'get_hotel_stats', []);
//      if (hotelData) {
//        this.state.hotelStats = hotelData;
//        this.state.bookingStatusRec = {
//          'status': hotelData['room'][0],
//          'count': hotelData['room'][1],
//        };
//        this.state.topCustomerRec = {
//          'partner': hotelData['top_customer'][0],
//          'amount': hotelData['top_customer'][1],
//        };
//        this.state.roomTypeRec = {
//          'stage': hotelData['get_cat_room'][0],
//          'count': hotelData['get_cat_room'][1],
//        };
//        this.state.monthBookingRec = {
//          'month': hotelData['booking_month'][0],
//          'count': hotelData['booking_month'][1],
//        };
//        this.state.dayBookingRec = {
//          'day': hotelData['booking_day'][0],
//          'confirm_count': hotelData['booking_day'][1],
//          'check_in_count': hotelData['booking_day'][2],
//          'check_out_count': hotelData['booking_day'][3],
//          'cancel_count': hotelData['booking_day'][4],
//        };
//      }
//    });
//    onMounted(() => {
//      this.renderBookingStatus(this.bookingStatus.el, this.state.bookingStatusRec);
//      this.renderTopCustomer(this.topCustomer.el, this.state.topCustomerRec);
//      this.renderMonthBooking();
//      this.renderDayBooking();
//    })
//  }
//  viewDashboardStatic(type) {
//    let model, domain, name;
//    let today = new Date();
//    let start = new Date(today);
//    let end = new Date(today.setDate(today.getDate() + 1));
//    start.setHours(0, 0, 0, 0);
//    end.setHours(0, 0, 0, 0);
//    if (type === 'active_room') {
//      model = 'hotel.booking'
//      domain = ['|', ['stages', '=', 'Confirm'], ['stages', '=', 'check_in']]
//      name = 'Active Room Booking'
//    } else if (type == 'active_hall') {
//      model = 'hotel.feast'
//      domain = [['stages', '=', 'Confirm']]
//      name = 'Active Hall Booking'
//    } else if (type == 'today_check_in') {
//      model = 'hotel.room.details'
//      domain = [['check_in', '>=', start], ['check_in', '<', end], ['stages', '=', 'Booked']]
//      name = 'Today Check-in'
//    } else if (type == 'today_check_out') {
//      model = 'hotel.room.details'
//      domain = [['check_out', '>=', start], ['check_out', '<', end], ['stages', '=', 'Booked']]
//      name = 'Today Check-out'
//    } else if (type == 'food') {
//      model = 'hotel.restaurant'
//      domain = [['stages', '=', 'Confirm']]
//      name = 'Food'
//    } else if (type == 'transport') {
//      model = 'hotel.transport'
//      domain = [['stage', '=', 'pending']]
//      name = 'Transport'
//    }
//    this.action.doAction({
//      type: 'ir.actions.act_window',
//      name: name,
//      res_model: model,
//      view_mode: 'list',
//      views: [[false, 'list'], [false, 'form']],
//      target: 'current',
//      context: { 'create': false },
//      domain: domain,
//    });
//  }
//
//  renderBookingStatus(div, sessionData) {
//    const root = am5.Root.new(div);
//    root.setThemes([
//      am5themes_Animated.new(root)
//    ]);
//
//    const chart = root.container.children.push(am5xy.XYChart.new(root, {
//      panX: true,
//      panY: true,
//      wheelX: "panX",
//      wheelY: "zoomX",
//      pinchZoomX: true,
//      paddingLeft: 0,
//      paddingRight: 1
//    }));
//
//    const cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
//    cursor.lineY.set("visible", false);
//
//    const xRenderer = am5xy.AxisRendererX.new(root, {
//      minGridDistance: 20,
//      minorGridEnabled: true
//    });
//
//    xRenderer.labels.template.setAll({
//      rotation: 0,
//      centerY: am5.p50,
//      centerX: am5.p50,
//    });
//
//    xRenderer.grid.template.setAll({
//      location: 1
//    })
//
//    let xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
//      maxDeviation: 0.3,
//      categoryField: "country",
//      renderer: xRenderer,
//      tooltip: am5.Tooltip.new(root, {})
//    }));
//
//    const yRenderer = am5xy.AxisRendererY.new(root, {
//      strokeOpacity: 0.1
//    })
//
//    let yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
//      maxDeviation: 0.3,
//      renderer: yRenderer
//    }));
//
//    let series = chart.series.push(am5xy.ColumnSeries.new(root, {
//      name: "Series 1",
//      xAxis: xAxis,
//      yAxis: yAxis,
//      valueYField: "value",
//      sequencedInterpolation: true,
//      categoryXField: "country",
//      tooltip: am5.Tooltip.new(root, {
//        labelText: "{valueY}"
//      })
//    }));
//
//    series.columns.template.setAll({ cornerRadiusTL: 5, cornerRadiusTR: 5, strokeOpacity: 0 });
//    series.columns.template.adapters.add("fill", function (fill, target) {
//      return chart.get("colors").getIndex(series.columns.indexOf(target));
//    });
//
//    series.columns.template.adapters.add("stroke", function (stroke, target) {
//      return chart.get("colors").getIndex(series.columns.indexOf(target));
//    });
//
//    let data = [];
//    for (let i = 0; i < sessionData['status'].length; i++) {
//
//      data.push({
//        value: sessionData['count'][i],
//        country: sessionData['status'][i],
//      })
//    }
//
//    xAxis.data.setAll(data);
//    series.data.setAll(data);
//
//    series.appear(1000);
//    chart.appear(1000, 100);
//  }
//
//  renderTopCustomer(div, sessionData) {
//    const root = am5.Root.new(div);
//
//    root.setThemes([
//      am5themes_Animated.new(root)
//    ]);
//
//    const chart = root.container.children.push(am5percent.PieChart.new(root, {
//      layout: root.verticalLayout
//    }));
//
//    let series = chart.series.push(am5percent.PieSeries.new(root, {
//      alignLabels: true,
//      calculateAggregates: true,
//      valueField: "value",
//      categoryField: "category"
//    }));
//
//    series.slices.template.setAll({
//      strokeWidth: 3,
//      stroke: am5.color(0xffffff)
//    });
//
//    series.labelsContainer.set("paddingTop", 30)
//
//    series.slices.template.adapters.add("radius", function (radius, target) {
//      let dataItem = target.dataItem;
//      let high = series.getPrivate("valueHigh");
//
//      if (dataItem) {
//        let value = target.dataItem.get("valueWorking", 0);
//        return radius * value / high
//      }
//      return radius;
//    });
//
//    series.get("colors").set("colors", [
//      am5.color("#f29494"),
//      am5.color("#c6ace3"),
//      am5.color("#f5c6a2"),
//      am5.color("#8bc9c6"),
//      am5.color("#d9d9b2")
//    ]);
//
//    let chartData = []
//    for (let i = 0; i < sessionData['partner'].length; i++) {
//      chartData.push({
//        value: sessionData['amount'][i],
//        category: sessionData['partner'][i],
//      })
//    }
//    series.data.setAll(chartData);
//
//    series.slices.template.set("tooltipText", "{category}: {value}");
//
//    const legend = chart.children.push(am5.Legend.new(root, {
//      centerX: am5.p50,
//      x: am5.p50,
//      marginTop: 15,
//      marginBottom: 15
//    }));
//
//    legend.data.setAll(series.dataItems);
//
//    series.appear(1000, 100);
//  }
//
//  //    renderRoomType() {
//  //        const options = {
//  //            series: this.state.roomTypeRec['count'],
//  //            chart: {
//  //                type: 'pie',
//  //                height: 410
//  //            },
//  //            colors: ['#F7A4A4', '#344D67', '#B6E2A1', '#FEBE8C'],
//  //            dataLabels: {
//  //                enabled: false
//  //            },
//  //            labels: this.state.roomTypeRec['stage'],
//  //            legend: {
//  //                position: 'bottom',
//  //            },
//  //        };
//  //        this.renderGraph(this.roomType.el, options);
//  //    }
//
//  renderMonthBooking() {
//    const options = {
//      series: [{
//        name: 'Booking',
//        data: this.state.monthBookingRec['count']
//      }],
//      chart: {
//        height: 350,
//      },
//      xaxis: {
//        categories: this.state.monthBookingRec['month'],
//      },
//      fill: {
//        type: 'gradient',
//        gradient: {
//          shade: 'dark',
//          gradientToColors: ['#FDD835'],
//          shadeIntensity: 1,
//          type: 'horizontal',
//          opacityFrom: 1,
//          opacityTo: 1,
//          stops: [0, 100, 100, 100]
//        },
//      }
//    };
//    this.renderGraph(this.monthBooking.el, options);
//  }
//
//  renderDayBooking() {
//    var options = {
//      series: [{
//        name: 'Confirmed Bookings',
//        data: this.state.dayBookingRec['confirm_count']
//      }, {
//        name: 'Checked In Bookings',
//        data: this.state.dayBookingRec['check_in_count']
//      }, {
//        name: 'Checked Out Bookings',
//        data: this.state.dayBookingRec['check_out_count']
//      }, {
//        name: 'Cancelled Bookings',
//        data: this.state.dayBookingRec['cancel_count']
//      }],
//      chart: {
//        type: 'bar',
//        height: 350,
//        stacked: true,
//        toolbar: {
//          show: true
//        },
//        zoom: {
//          enabled: true
//        }
//      },
//      colors: ['#DE63A2', '#64B1FA', '#10A19D', '#98BE55'],
//      responsive: [{
//        breakpoint: 480,
//        options: {
//          legend: {
//            position: 'bottom',
//            offsetX: -10,
//            offsetY: 0
//          }
//        }
//      }],
//      plotOptions: {
//            bar: {
//                horizontal: false,
//                borderRadius: 10,
//                dataLabels: {
//                    total: {
//                        enabled: true,
//                        style: {
//                            fontSize: '13px',
//                            fontWeight: 900,
//                        }
//                    }
//                }
//            },
//        },
//        dataLabels: {
//            style: {
//                fontSize: '12px',
//                fontFamily: 'Helvetica, Arial, sans-serif',
//                fontWeight: 'normal',
//                colors: ['#292828']
//            },
//        },
//      xaxis: {
//        type: 'datetime',
//        categories: this.state.dayBookingRec['day'],
//      },
//      legend: {
//        position: 'bottom',
//        offsetY: 10
//      },
//      fill: {
//        opacity: 1
//      }
//    };
//    this.renderGraph(this.dayBooking.el, options);
//  }
//
//  renderGraph(el, options) {
//    const graphData = new ApexCharts(el, options);
//    graphData.render();
//  }
//
//}
RoomDashboard.template = "tk_hotel_management.room_dashboard";
registry.category("actions").add("hotel_room_dashboard", RoomDashboard);
//HotelDashboard.template = "tk_hotel_management.hotel_dashboard";
//registry.category("actions").add("hotel_dashboard", HotelDashboard);
