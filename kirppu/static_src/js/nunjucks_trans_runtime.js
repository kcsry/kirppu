function Trans() {
    this.run = function(context, text) {
        return gettext(text);
    };
}

if (typeof(module) !== "undefined" && typeof(module.exports) !== "undefined") {
    module.exports.Trans = Trans;
}
