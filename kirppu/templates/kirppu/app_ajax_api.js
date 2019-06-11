(function() {
    const api = {};
{% for name, f in funcs %}
api['{{ name }}'] = function(params) {
    return $.ajax({
        type: '{{ f.method }}',
        url:  '{% url f.view event.slug %}',
        data: params
    });
};
{% endfor %}
    window.{{ api_name }} = api;
}).call(this);
