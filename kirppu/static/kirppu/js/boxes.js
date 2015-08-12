// ================ 1: number_test.coffee ================

(function() {
  var NUM_PAT;

  NUM_PAT = /^-?\d+([,\.]\d*)?$/;

  Number.isConvertible = function(str) {
    return NUM_PAT.test(str);
  };

}).call(this);

// ================ 2: boxes.coffee ================

(function() {
  var BoxesConfig, C, addBox, bindBoxEvents, bindBoxHideEvents, bindBoxPrintEvents, bindFormEvents, createBox, hideBox, isPrinted, onPriceChange, printBox, warnAlreadyPrinted;

  BoxesConfig = (function() {
    BoxesConfig.prototype.url_args = {
      box_id: ''
    };

    BoxesConfig.prototype.urls = {
      roller: '',
      box_add: '',
      box_content: '',
      box_hide: '',
      box_print: ''
    };

    BoxesConfig.prototype.enabled = true;

    function BoxesConfig() {}

    BoxesConfig.prototype.box_content_url = function(box_id) {
      var url;
      url = this.urls.box_content;
      return url.replace(this.url_args.box_id, box_id);
    };

    BoxesConfig.prototype.box_hide_url = function(box_id) {
      var url;
      url = this.urls.box_hide;
      return url.replace(this.url_args.box_id, box_id);
    };

    BoxesConfig.prototype.box_print_url = function(box_id) {
      var url;
      url = this.urls.box_print;
      return url.replace(this.url_args.box_id, box_id);
    };

    return BoxesConfig;

  })();

  C = new BoxesConfig;

  createBox = function(box_id, description, item_count, item_price, vendor_id, item_type, item_adult) {
    var box;
    box = $(".box_template").clone();
    box.removeClass("box_template");
    box.addClass("box_short");
    $('.box_description', box).text(description);
    $('.box_count', box).text(item_count);
    $('.box_price', box).text(item_price);
    $('.box_type', box).text(item_type);
    if (item_adult === "yes") {
      $('.box_adult', box).text("K-18");
    } else {
      $('.box_adult', box).text("-");
    }
    $('.box_vendor_id', box).text(vendor_id);
    $(box).attr('id', box_id);
    return box;
  };

  addBox = function() {
    var content, onError, onSuccess;
    onSuccess = function(box) {
      $('#form-errors').empty();
      box = createBox(box.box_id, box.description, box.item_count, box.item_price, box.vendor_id, box.item_type, box.item_adult);
      $('#box-add-form')[0].reset();
      $('#boxes').prepend(box);
      return bindBoxEvents($(box));
    };
    onError = function(jqXHR, textStatus, errorThrown) {
      $('#form-errors').empty();
      if (jqXHR.responseText) {
        return $('<p>').text(jqXHR.responseText).appendTo($('#form-errors'));
      }
    };
    content = {
      description: $("#box-add-description").val(),
      name: $("#box-add-itemtitle").val(),
      count: $("#box-add-count").val(),
      price: $("#box-add-price").val(),
      item_type: $("#box-add-itemtype").val(),
      adult: $("input[name=box-add-adult]:checked").val()
    };
    return $.ajax({
      url: C.urls.box_add,
      type: 'POST',
      data: content,
      success: onSuccess,
      error: onError
    });
  };

  hideBox = function(box, box_id) {
    return $.ajax({
      url: C.box_hide_url(box_id),
      type: 'POST',
      success: function() {
        return $(box).remove();
      },
      error: function() {
        return $(box).show('slow');
      }
    });
  };

  printBox = function(box, box_id) {
    var printFunc;
    printFunc = function() {
      window.open(C.box_content_url(box_id), '_blank');
      return $.ajax({
        url: C.box_print_url(box_id),
        type: 'POST',
        success: function() {
          return $('#print_box', box).removeClass("btn-success");
        }
      });
    };
    if (isPrinted(box)) {
      return warnAlreadyPrinted(printFunc);
    } else {
      return printFunc();
    }
  };

  warnAlreadyPrinted = function(print) {
    var result;
    result = confirm(gettext('This box has been already printed. Are you sure you want to print it again?'));
    if (result) {
      return print();
    }
  };

  isPrinted = function(box) {
    return !$('#print_box', box).hasClass("btn-success");
  };

  onPriceChange = function() {
    var formGroup, input, value;
    input = $(this);
    formGroup = input.parents(".form-group");
    value = input.val().replace(',', '.');
    if (value > 400 || value <= 0 || !Number.isConvertible(value)) {
      formGroup.addClass('has-error');
    } else {
      formGroup.removeClass('has-error');
    }
  };

  bindFormEvents = function() {
    $('#box-add-form').bind('submit', function() {
      addBox();
      return false;
    });
    $('#box-add-price').change(onPriceChange);
  };

  bindBoxEvents = function(boxes) {
    boxes.each(function(index, box) {
      var box_id;
      box = $(box);
      box_id = box.attr('id');
      bindBoxHideEvents(box, box_id);
      bindBoxPrintEvents(box, box_id);
    });
  };

  bindBoxHideEvents = function(box, box_id) {
    return $('.box_button_hide', box).click(function() {
      return $(box).hide('slow', function() {
        return hideBox(box, box_id);
      });
    });
  };

  bindBoxPrintEvents = function(box, box_id) {
    return $('#print_box', box).click(function() {
      return printBox(box, box_id);
    });
  };

  window.boxesConfig = C;

  window.addBox = addBox;

  window.printBox = printBox;

  window.bindBoxEvents = bindBoxEvents;

  window.bindFormEvents = bindFormEvents;

}).call(this);
