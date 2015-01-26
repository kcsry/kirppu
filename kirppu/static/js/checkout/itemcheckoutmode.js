// Generated by CoffeeScript 1.7.1
(function() {
  var __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  this.ItemCheckoutMode = (function(_super) {
    __extends(ItemCheckoutMode, _super);

    function ItemCheckoutMode() {
      ItemCheckoutMode.__super__.constructor.apply(this, arguments);
      this.receipt = new ItemReceiptTable();
    }

    ItemCheckoutMode.prototype.enter = function() {
      ItemCheckoutMode.__super__.enter.apply(this, arguments);
      return this.cfg.uiRef.body.append(this.receipt.render());
    };

    ItemCheckoutMode.prototype.createRow = function(index, code, name, price, rounded) {
      var row, x, _i, _len, _ref;
      if (price == null) {
        price = null;
      }
      if (rounded == null) {
        rounded = false;
      }
      row = $('<tr id="' + code + '">');
      _ref = [index, code, name, displayPrice(price, rounded)];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        x = _ref[_i];
        row.append($("<td>").text(x));
      }
      return row;
    };

    return ItemCheckoutMode;

  })(CheckoutMode);

}).call(this);