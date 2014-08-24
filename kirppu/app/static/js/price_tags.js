// Generated by CoffeeScript 1.7.1
(function() {
  var C, L, LocalizationStrings, PriceTagsConfig, addItem, bindFormEvents, bindItemToListEvents, bindItemToPrintEvents, bindItemToggleEvents, bindListTagEvents, bindNameEditEvents, bindPriceEditEvents, bindTagEvents, createTag, deleteAll, deleteIsDisabled, listViewIsOn, moveToList, moveToPrint, onClickToList, onClickToPrint, onPriceChange, toggleDelete, toggleListView, unbindTagEvents;

  LocalizationStrings = (function() {
    function LocalizationStrings() {}

    LocalizationStrings.prototype.toggleDelete = {
      enabledText: 'Disable mark button',
      disabledText: 'Mark individual items'
    };

    LocalizationStrings.prototype.deleteItem = {
      enabledTitle: 'Mark this item as printed.',
      disabledTitle: 'Mark this item as printed. Enable this button from the top of the page.'
    };

    LocalizationStrings.prototype.deleteAll = {
      confirmText: 'This will mark all items as printed so they can no longer be edited. Continue?'
    };

    return LocalizationStrings;

  })();

  L = new LocalizationStrings();

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
      barcode_img: '',
      item_to_print: '',
      all_to_print: ''
    };

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

    PriceTagsConfig.prototype.barcode_img_url = function(code) {
      var url;
      url = this.urls.barcode_img;
      return url.replace(this.url_args.code, code);
    };

    PriceTagsConfig.prototype.item_to_print_url = function(code) {
      var url;
      url = this.urls.item_to_print;
      return url.replace(this.url_args.code, code);
    };

    return PriceTagsConfig;

  })();

  C = new PriceTagsConfig;

  createTag = function(name, price, vendor_id, code, type) {
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
    $('.item_vendor_id', tag).text(vendor_id);
    $(tag).attr('id', code);
    $('.item_extra_code', tag).text(code);
    $('.barcode_container > img', tag).attr('src', C.barcode_img_url(code));
    return tag;
  };

  addItem = function() {
    var content, onSuccess;
    onSuccess = function(items) {
      var item, tag, _i, _len, _results;
      _results = [];
      for (_i = 0, _len = items.length; _i < _len; _i++) {
        item = items[_i];
        tag = createTag(item.name, item.price, item.vendor_id, item.code, item.type);
        $('#items').prepend(tag);
        _results.push(bindTagEvents($(tag)));
      }
      return _results;
    };
    content = {
      name: $("#item-add-name").val(),
      price: $("#item-add-price").val(),
      range: $("#item-add-suffixes").val(),
      type: $("input[name=item-add-type]:checked").val()
    };
    return $.post(C.urls.item_add, content, onSuccess);
  };

  deleteAll = function() {
    var tags;
    if (!confirm(L.deleteAll.confirmText)) {
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
          code = $(".item_extra_code", tag).text();
          return moveToList(tag, code);
        });
      },
      error: function() {
        return $(tags).show('slow');
      }
    });
  };

  deleteIsDisabled = false;

  toggleDelete = function() {
    var deleteButtons, toggleButton;
    deleteIsDisabled = deleteIsDisabled ? false : true;
    toggleButton = $('#toggle_delete');
    if (deleteIsDisabled) {
      toggleButton.removeClass('active');
      toggleButton.addClass('btw-default');
    } else {
      toggleButton.removeClass('btw-default');
      toggleButton.addClass('active');
    }
    deleteButtons = $('.item_button_delete');
    if (deleteIsDisabled) {
      deleteButtons.attr('disabled', 'disabled');
      deleteButtons.attr('title', L.deleteItem.disabledTitle);
    } else {
      deleteButtons.removeAttr('disabled');
      deleteButtons.attr('title', L.deleteItem.enabledTitle);
    }
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
    if (value > 400 || value <= 0 || Number.isNaN(Number.parseInt(value))) {
      formGroup.addClass('has-error');
    } else {
      formGroup.removeClass('has-error');
    }
  };

  bindFormEvents = function() {
    $('#add_short_item').click(addItem);
    $('#delete_all').click(deleteAll);
    $('#toggle_delete').click(toggleDelete);
    $('#list_view').click(toggleListView);
    toggleDelete();
    $('#item-add-price').change(onPriceChange);
  };

  bindPriceEditEvents = function(tag, code) {
    $(".item_price", tag).editable(C.price_update_url(code), {
      indicator: "<img src='" + C.urls.roller + "'>",
      tooltip: "Click to edit...",
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
      tooltip: "Click to edit...",
      onblur: "submit",
      style: "inherit"
    });
  };

  moveToPrint = function(tag, code) {
    $.ajax({
      url: C.item_to_print_url(code),
      type: 'POST',
      success: function(item) {
        var new_tag;
        $(tag).remove();
        new_tag = createTag(item.name, item.price, item.vendor_id, item.code, item.type);
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

  moveToList = function(tag, code) {
    $.ajax({
      url: C.item_to_list_url(code),
      type: 'POST',
      success: function() {
        unbindTagEvents($(tag));
        $('.item_button_delete', tag).click(function() {
          return onClickToPrint(tag, code);
        });
        $(tag).prependTo("#printed_items");
        $(tag).addClass("item_list");
        return $(tag).show('slow');
      },
      error: function() {
        return $(tag).show('slow');
      }
    });
  };

  onClickToList = function(tag, code) {
    return $(tag).hide('slow', function() {
      return moveToList(tag, code);
    });
  };

  onClickToPrint = function(tag, code) {
    return $(tag).hide('slow', function() {
      return moveToPrint(tag, code);
    });
  };

  bindItemToListEvents = function(tag, code) {
    $('.item_button_delete', tag).click(function() {
      return onClickToList(tag, code);
    });
  };

  bindItemToPrintEvents = function(tag, code) {
    $('.item_button_delete', tag).click(function() {
      return onClickToPrint(tag, code);
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
      code = $(".item_extra_code", tag).text();
      bindPriceEditEvents(tag, code);
      bindNameEditEvents(tag, code);
      bindItemToListEvents(tag, code);
      bindItemToggleEvents(tag, code);
    });
  };

  bindListTagEvents = function(tags) {
    tags.each(function(index, tag) {
      var code;
      code = $(".item_extra_code", tag).text();
      bindItemToPrintEvents(tag, code);
    });
  };

  unbindTagEvents = function(tags) {
    tags.each(function(index, tag) {
      $('.item_name', tag).unbind('click');
      $('.item_price', tag).unbind('click');
      $('.item_button_toggle', tag).unbind('click');
      $('.item_button_delete', tag).unbind('click');
    });
  };

  window.localization = L;

  window.itemsConfig = C;

  window.addItem = addItem;

  window.deleteAll = deleteAll;

  window.toggleDelete = toggleDelete;

  window.bindTagEvents = bindTagEvents;

  window.bindListTagEvents = bindListTagEvents;

  window.bindFormEvents = bindFormEvents;

}).call(this);
