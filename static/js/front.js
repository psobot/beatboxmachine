(function() {
  var addPlayer, counter, firsttitle, lastwidth, loaded, manualSeek, watch;
  manualSeek = false;
  loaded = false;
  addPlayer = function(filename) {};
  window.log = function() {
    log.history = log.history || [];
    log.history.push(arguments);
    if (this.console) {
      return console.log(Array.prototype.slice.call(arguments));
    }
  };
  counter = 0;
  firsttitle = document.title;
  lastwidth = 0;
  $(document).ready(function() {});
  /$(".qq-upload-button").remove()uploader=newqq.FileUploader(element:document.getElementById("file-uploader")action:"upload"allowedExtensions:window.wubconfig.allowed_file_extensionsdebug:falseonSubmit:(id,fileName)->$("#file-uploader").remove()$(".progress").show()$(".progress.text").show()$(".progress.text").html"Uploadingsong..."document.title="Uploadingsong..."onProgress:(id,fileName,loaded,total)->$(".progress").width((loaded\/total)*100)+"%"document.title="Uploading:"+Math.round((loaded\/total)*100)+"%"onComplete:(id,fileName,r)->ifr.success$(".progress.text").show()$(".progress.text").htmlr.text$(".progress.number").show()window.wubconfig.uid=r.uid$(".progress").width0document.title="Waiting..."$(".link").slideDown()watchr.uidelsewindow.log"Somethingwentwrong.",fileName,runlessr.response$(".progress.text").html"Sorry,thatsongdidn'twork.Tryanother!"else$(".progress.text").html"Hmm...somethingwentwrongthere.Tryagain!"onCancel:(id,fileName)->showMessage:(message)->a=$(".qq-upload-buttoninput")$(".qq-upload-button").htmlmessage$(".qq-upload-button").appenda)/;
  window.uploading = function() {
    $("#clicktorecord").fadeOut();
    return $("#uploading").slideDown();
  };
  window.serverResponse = function(r) {
    window.log(r);
    $("#uploading").slideUp();
    $("#file-uploader").remove();
    $(".progress").show();
    $(".progress .text").show();
    $(".progress .text").html("Uploading song...");
    document.title = "Uploading song...";
    if (r.success) {
      $(".progress .text").show();
      $(".progress .text").html(r.text);
      $(".progress .number").show();
      window.wubconfig.uid = r.uid;
      $(".progress").width(0);
      document.title = "Waiting...";
      $(".link").slideDown();
      watch(r.uid);
    } else {
      window.log("Something went wrong.", fileName, r);
      if (!r.response) {
        $(".progress .text").html("Sorry, that song didn't work. Try another!");
      } else {
        $(".progress .text").html("Hmm... something went wrong there. Try again!");
      }
    }
    return 1;
  };
  watch = function(uid) {
    var s;
    s = new io.Socket(window.location.hostname, {
      port: window.wubconfig.socket_io_port,
      resource: window.wubconfig.progress_resource + window.wubconfig.socket_extra_sep + uid,
      rememberTransport: window.wubconfig.remember_transport,
      reconnect: false
    });
    s.connect();
    return s.on('message', function(data) {
      var displayTag, html;
      $('.progress .text').html(data.text);
      switch (data.status) {
        case -1:
          $(".progress").animate({
            width: 0
          });
          window.log("Error", data);
          return document.title = "Error!";
        case 0:
          return document.title = "Waiting...";
        case 1:
          $('.progress').animate({
            width: (data.progress * 100) + "%"
          });
          document.title = Math.round(data.progress * 100, 2) + "% - " + data.text;
          displayTag = (data.tag.title != null) && data.tag.title !== '';
          if (!$("#precontent").is(":visible")) {
            if (displayTag) {
              $("#precontent").html("Currently remixing <strong>" + data.tag.title + "</strong>" + (data.tag.artist != null ? " by " + data.tag.artist + "..." : void 0));
              $("#precontent").slideDown();
            }
          }
          if (data.progress === 1) {
            s.disconnect();
            document.title = "Done!";
            html = "<div class='ui360 ui360-vis " + (!displayTag ? 'center' : void 0) + "'><a href='" + data.tag.remixed + "'></a></div>";
            if (data.tag.art != null) {
              html += "<div id='art'><img src='" + data.tag.thumbnail + "' alt='" + data.tag.album + "' title='wubwubwub!' /></div>";
            }
            if (displayTag) {
              html += "<div id='tag' class='trackviewer'><strong>" + data.tag.new_title + "</strong><br />by " + data.tag.artist + "<br />from <em>" + data.tag.album + "<em></div>";
            }
            html = "<div id='player'>" + html + "</div>";
            $(html).insertBefore('.progress');
            window.soundManager.reboot();
            $("#content").animate({
              border: 0
            });
            $("#post").slideDown();
            $(".error, #checkout, #precontent, .link").slideUp(function() {
              return $(this).remove();
            });
            $(".progress").fadeOut(function() {
              return $("#player").slideDown();
            });
            $(".download a").attr("href", "download/" + data.uid);
            if (displayTag) {
              return document.title = data.tag.new_title;
            }
          }
      }
    });
  };
}).call(this);
