(function() {
    var {{ api_name }} = {};
{% for name, f in funcs %}

{{ api_name }}['{{ name }}'] = function(params) {
    return $.ajax({
        type: '{{ f.method }}',
        url:  '{% url f.view %}',
        data: params
    });
};

{% endfor %}
    window.{{ api_name }} = {{ api_name }};
}).call(this);
