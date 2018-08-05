if(!window.gettext) {
    window.gettext = function(s) { return s; };
}
if (!window.pgettext) {
    window.pgettext = function(c, s) { return s; };
}
if (!window.ngettext) {
    window.ngettext = function(s, m, c) { return (c === 1) ? s : m; }
}
