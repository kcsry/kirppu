function Trans() {
    this.run = function(context, text) {
        return new nunjucks.runtime.SafeString(gettext(text));
    };
}

if (typeof(module) !== "undefined" && typeof(module.exports) !== "undefined") {
    module.exports.Trans = Trans;
}
