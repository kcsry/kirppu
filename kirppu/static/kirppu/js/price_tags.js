// ================ 1: number_test.coffee ================

(function() {
  var NUM_PAT;

  NUM_PAT = /^-?\d+([,\.]\d*)?$/;

  Number.isConvertible = function(str) {
    return NUM_PAT.test(str);
  };

}).call(this);

// ================ 2: price_tags.coffee ================

(function() {
  var C, PriceTagsConfig, addItem, bindFormEvents, bindItemHideEvents, bindItemToNotPrintedEvents, bindItemToPrintedEvents, bindItemToggleEvents, bindListTagEvents, bindNameEditEvents, bindPriceEditEvents, bindTagEvents, createTag, deleteAll, hideItem, listViewIsOn, moveItemToNotPrinted, moveItemToPrinted, moveTagToPrinted, onPriceChange, toggleListView, unbindTagEvents;

  PriceTagsConfig = (function() {
    PriceTagsConfig.prototype.url_args = {
      code: ''
    };

    PriceTagsConfig.prototype.urls = {
      roller: '',
      name_update: '',
      price_update: '',
      item_to_list: '',
      size_update: '',
      item_add: '',
      item_hide: '',
      item_to_print: '',
      all_to_print: ''
    };

    PriceTagsConfig.prototype.enabled = true;

    PriceTagsConfig.prototype.price_min = 0;

    PriceTagsConfig.prototype.price_max = 400;

    function PriceTagsConfig() {}

    PriceTagsConfig.prototype.name_update_url = function(code) {
      var url;
      url = this.urls.name_update;
      return url.replace(this.url_args.code, code);
    };

    PriceTagsConfig.prototype.price_update_url = function(code) {
      var url;
      url = this.urls.price_update;
      return url.replace(this.url_args.code, code);
    };

    PriceTagsConfig.prototype.item_to_list_url = function(code) {
      var url;
      url = this.urls.item_to_list;
      return url.replace(this.url_args.code, code);
    };

    PriceTagsConfig.prototype.size_update_url = function(code) {
      var url;
      url = this.urls.size_update;
      return url.replace(this.url_args.code, code);
    };

    PriceTagsConfig.prototype.item_to_print_url = function(code) {
      var url;
      url = this.urls.item_to_print;
      return url.replace(this.url_args.code, code);
    };

    PriceTagsConfig.prototype.item_hide_url = function(code) {
      var url;
      url = this.urls.item_hide;
      return url.replace(this.url_args.code, code);
    };

    return PriceTagsConfig;

  })();

  C = new PriceTagsConfig;

  createTag = function(name, price, vendor_id, code, dataurl, type, adult) {
    var tag;
    tag = $(".item_template").clone();
    tag.removeClass("item_template");
    if (type === "short") {
      tag.addClass("item_short");
    }
    if (type === "tiny") {
      tag.addClass("item_tiny");
    }
    $('.item_name', tag).text(name);
    $('.item_price', tag).text(price);
    $('.item_head_price', tag).text(price);
    if (adult === "yes") {
      $('.item_adult_tag', tag).text("K-18");
    }
    $('.item_vendor_id', tag).text(vendor_id);
    $(tag).attr('id', code);
    $('.item_extra_code', tag).text(code);
    $('.barcode_container > img', tag).attr('src', dataurl);
    if (listViewIsOn) {
      tag.addClass('item_list');
    }
    return tag;
  };

  addItem = function() {
    var content, onError, onSuccess;
    onSuccess = function(items) {
      var i, item, len, results, tag;
      $('#form-errors').empty();
      results = [];
      for (i = 0, len = items.length; i < len; i++) {
        item = items[i];
        tag = createTag(item.name, item.price, item.vendor_id, item.code, item.barcode_dataurl, item.type, item.adult);
        $('#items').prepend(tag);
        results.push(bindTagEvents($(tag)));
      }
      return results;
    };
    onError = function(jqXHR, textStatus, errorThrown) {
      $('#form-errors').empty();
      if (jqXHR.responseText) {
        return $('<p>').text(jqXHR.responseText).appendTo($('#form-errors'));
      }
    };
    content = {
      name: $("#item-add-name").val(),
      price: $("#item-add-price").val(),
      suffixes: $("#item-add-suffixes").val(),
      tag_type: $("input[name=item-add-type]:checked").val(),
      item_type: $("#item-add-itemtype").val(),
      adult: $("input[name=item-add-adult]:checked").val()
    };
    return $.ajax({
      url: C.urls.item_add,
      type: 'POST',
      data: content,
      success: onSuccess,
      error: onError
    });
  };

  deleteAll = function() {
    var tags;
    if (!confirm(gettext("This will mark all items as printed so they won't be printed again accidentally. Continue?"))) {
      return;
    }
    tags = $('#items > .item_container');
    $(tags).hide('slow');
    $.ajax({
      url: C.urls.all_to_print,
      type: 'POST',
      success: function() {
        return $(tags).each(function(index, tag) {
          var code;
          code = $(tag).attr('id');
          return moveTagToPrinted(tag, code);
        });
      },
      error: function() {
        return $(tags).show('slow');
      }
    });
  };

  listViewIsOn = false;

  toggleListView = function() {
    var items;
    listViewIsOn = listViewIsOn ? false : true;
    items = $('#items > .item_container');
    if (listViewIsOn) {
      return items.addClass('item_list');
    } else {
      return items.removeClass('item_list');
    }
  };

  onPriceChange = function() {
    var formGroup, input, value;
    input = $(this);
    formGroup = input.parents(".form-group");
    value = input.val().replace(',', '.');
    if (value > C.price_max || value < C.price_min || !Number.isConvertible(value)) {
      formGroup.addClass('has-error');
    } else {
      formGroup.removeClass('has-error');
    }
  };

  bindFormEvents = function() {
    $('#item-add-form').bind('submit', function() {
      addItem();
      return false;
    });
    $('#print_items').click(function() {
      return window.print();
    });
    $('#delete_all').click(deleteAll);
    $('#list_view').click(toggleListView);
    $('#item-add-price').change(onPriceChange);
  };

  bindPriceEditEvents = function(tag, code) {
    $(".item_price", tag).editable(C.price_update_url(code), {
      indicator: "<img src='" + C.urls.roller + "'>",
      tooltip: gettext("Click to edit..."),
      placeholder: gettext("<em>Click to edit</em>"),
      onblur: "submit",
      style: "width: 2cm",
      callback: function(value) {
        return $(".item_head_price", tag).text(value);
      }
    });
  };

  bindNameEditEvents = function(tag, code) {
    $(".item_name", tag).editable(C.name_update_url(code), {
      indicator: "<img src='" + C.urls.roller + "'>",
      tooltip: gettext("Click to edit..."),
      placeholder: gettext("<em>Click to edit</em>"),
      onblur: "submit",
      style: "inherit"
    });
  };

  hideItem = function(tag, code) {
    return $.ajax({
      url: C.item_hide_url(code),
      type: 'POST',
      success: function() {
        return $(tag).remove();
      },
      error: function() {
        return $(tag).show('slow');
      }
    });
  };

  bindItemHideEvents = function(tag, code) {
    return $('.item_button_hide', tag).click(function() {
      return $(tag).hide('slow', function() {
        return hideItem(tag, code);
      });
    });
  };

  moveItemToNotPrinted = function(tag, code) {
    $.ajax({
      url: C.item_to_print_url(code),
      type: 'POST',
      success: function(item) {
        var new_tag;
        $(tag).remove();
        new_tag = createTag(item.name, item.price, item.vendor_id, item.code, item.barcode_dataurl, item.type, item.adult);
        $(new_tag).hide();
        $(new_tag).appendTo("#items");
        $(new_tag).show('slow');
        return bindTagEvents($(new_tag));
      },
      error: function(item) {
        return $(tag).show('slow');
      }
    });
  };

  moveTagToPrinted = function(tag, code) {
    unbindTagEvents($(tag));
    $('.item_button_printed', tag).click(function() {
      return $(tag).hide('slow', function() {
        return moveItemToNotPrinted(tag, code);
      });
    });
    $(tag).prependTo("#printed_items");
    $(tag).addClass("item_list");
    $(tag).show('slow');
  };

  moveItemToPrinted = function(tag, code) {
    $.ajax({
      url: C.item_to_list_url(code),
      type: 'POST',
      success: function() {
        return moveTagToPrinted(tag, code);
      },
      error: function() {
        return $(tag).show('slow');
      }
    });
  };

  bindItemToPrintedEvents = function(tag, code) {
    $('.item_button_printed', tag).click(function() {
      return $(tag).hide('slow', function() {
        return moveItemToPrinted(tag, code);
      });
    });
  };

  bindItemToNotPrintedEvents = function(tag, code) {
    $('.item_button_printed', tag).click(function() {
      return $(tag).hide('slow', function() {
        return moveItemToNotPrinted(tag, code);
      });
    });
  };

  bindItemToggleEvents = function(tag, code) {
    var getNextType, onItemSizeToggle, setTagType;
    setTagType = function(tag_type) {
      if (tag_type === "tiny") {
        $(tag).addClass('item_tiny');
      } else {
        $(tag).removeClass('item_tiny');
      }
      if (tag_type === "short") {
        $(tag).addClass('item_short');
      } else {
        $(tag).removeClass('item_short');
      }
    };
    getNextType = function(tag_type) {
      tag_type = (function() {
        switch (tag_type) {
          case "tiny":
            return "short";
          case "short":
            return "long";
          case "long":
            return "tiny";
          default:
            return "short";
        }
      })();
      return tag_type;
    };
    onItemSizeToggle = function() {
      var new_tag_type, tag_type;
      if ($(tag).hasClass('item_short')) {
        tag_type = "short";
      } else if ($(tag).hasClass('item_tiny')) {
        tag_type = "tiny";
      } else {
        tag_type = "long";
      }
      new_tag_type = getNextType(tag_type);
      setTagType(new_tag_type);
      $.ajax({
        url: C.size_update_url(code),
        type: 'POST',
        data: {
          tag_type: new_tag_type
        },
        complete: function(jqXHR, textStatus) {
          if (textStatus !== "success") {
            return setTagType(tag_type);
          }
        }
      });
    };
    $('.item_button_toggle', tag).click(onItemSizeToggle);
  };

  bindTagEvents = function(tags) {
    tags.each(function(index, tag) {
      var code;
      tag = $(tag);
      code = tag.attr('id');
      if (C.enabled) {
        bindPriceEditEvents(tag, code);
        bindNameEditEvents(tag, code);
      } else {
        tag.removeClass("item_editable");
      }
      bindItemHideEvents(tag, code);
      bindItemToPrintedEvents(tag, code);
      bindItemToggleEvents(tag, code);
    });
  };

  bindListTagEvents = function(tags) {
    tags.each(function(index, tag) {
      var code;
      code = $(tag).attr('id');
      bindItemToNotPrintedEvents(tag, code);
    });
  };

  unbindTagEvents = function(tags) {
    tags.each(function(index, tag) {
      $('.item_name', tag).unbind('click');
      $('.item_price', tag).unbind('click');
      $('.item_button_toggle', tag).unbind('click');
      $('.item_button_printed', tag).unbind('click');
    });
  };

  window.itemsConfig = C;

  window.addItem = addItem;

  window.deleteAll = deleteAll;

  window.bindTagEvents = bindTagEvents;

  window.bindListTagEvents = bindListTagEvents;

  window.bindFormEvents = bindFormEvents;

}).call(this);
