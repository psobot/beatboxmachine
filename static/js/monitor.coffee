nonzero = (series) ->
  for x in series
    if x[1] != 0
      return true
  return false

$(document).ready( ->
  s = new io.Socket(window.location.hostname,
    port: window.wubconfig.socket_io_port
    rememberTransport: window.wubconfig.remember_transport
    resource: window.wubconfig.monitor_resource
  )
  s.connect()
  s.on "message", (result) ->
    target = $("#" + $(result).attr('id'))
    if target.length
      target.replaceWith(result)
    else
      $("#latest").prepend(result)
    

  $.getJSON("/monitor/graph", (songs) ->
    types =
      'Finished': songs.remixTrue
      'Failed': songs.remixFalse
      'Shared': songs.shareTrue
      'Failed Sharing': songs.shareFalse
      'Downloaded': songs.download
    graphData = for name, data of types
      {type: 'line', name: name, data: data, visible: (nonzero(data))}
    frequency = new Highcharts.Chart
      chart:
        renderTo: 'songs',
        plotBackgroundColor: null
        plotBorderWidth: null
        plotShadow: false
        zoomType: 'x'
      title:
        text: 'Logs & Stats for the Wub Machine'
      xAxis:
        type: 'datetime',
        tickInterval: 3600 * 1000 * 24
        tickWidth: 0
        gridLineWidth: 1
        maxZoom: 6 * 3600000
      yAxis:
        title:
          text: "Number of Songs"
        min: 0
      plotOptions:
        line:
          allowPointSelect: true
          cursor: 'pointer'
      series: graphData
  )
)


