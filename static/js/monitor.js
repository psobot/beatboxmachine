(function() {
  var nonzero;
  nonzero = function(series) {
    var x, _i, _len;
    for (_i = 0, _len = series.length; _i < _len; _i++) {
      x = series[_i];
      if (x[1] !== 0) {
        return true;
      }
    }
    return false;
  };
  $(document).ready(function() {
    var s;
    s = new io.Socket(window.location.hostname, {
      port: window.wubconfig.socket_io_port,
      rememberTransport: window.wubconfig.remember_transport,
      resource: window.wubconfig.monitor_resource
    });
    s.connect();
    s.on("message", function(result) {
      var target;
      target = $("#" + $(result).attr('id'));
      if (target.length) {
        return target.replaceWith(result);
      } else {
        return $("#latest").prepend(result);
      }
    });
    return $.getJSON("/monitor/graph", function(songs) {
      var data, frequency, graphData, name, types;
      types = {
        'Finished': songs.remixTrue,
        'Failed': songs.remixFalse,
        'Shared': songs.shareTrue,
        'Failed Sharing': songs.shareFalse,
        'Downloaded': songs.download
      };
      graphData = (function() {
        var _results;
        _results = [];
        for (name in types) {
          data = types[name];
          _results.push({
            type: 'line',
            name: name,
            data: data,
            visible: nonzero(data)
          });
        }
        return _results;
      })();
      return frequency = new Highcharts.Chart({
        chart: {
          renderTo: 'songs',
          plotBackgroundColor: null,
          plotBorderWidth: null,
          plotShadow: false,
          zoomType: 'x'
        },
        title: {
          text: 'Logs & Stats for the Wub Machine'
        },
        xAxis: {
          type: 'datetime',
          tickInterval: 3600 * 1000 * 24,
          tickWidth: 0,
          gridLineWidth: 1,
          maxZoom: 6 * 3600000
        },
        yAxis: {
          title: {
            text: "Number of Songs"
          },
          min: 0
        },
        plotOptions: {
          line: {
            allowPointSelect: true,
            cursor: 'pointer'
          }
        },
        series: graphData
      });
    });
  });
}).call(this);
