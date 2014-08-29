from django.conf.urls import patterns, url, include

__author__ = 'jyrkila'

urlpatterns = patterns('kirppu.app.views',
    url(r'^clerks/?$', 'get_clerk_codes', name='clerks'),
    url(r'^command/(?P<data>::\w+?)\.(?P<ext>\w+)$',
        'get_barcode', name='command_barcode'),
    url(r'^barcode/(?P<data>\w+?)\.(?P<ext>\w+)$',
        'get_barcode', name='barcode'),
    url(r'^checkout/$', 'checkout_view'),

    url(r'^vendor/$', 'vendor_view', name='vendor_view'),

    url(r'^vendor/items/?$', 'get_items', name='page'),
    url(r'^vendor/items/move_to_print$', 'all_to_print', name='all_to_print'),

    url(r'^vendor/item/$', 'item_add', name='item_add'),
    url(r'^vendor/item/(?P<code>\w+?)/to_list$', 'item_to_list', name='item_to_list'),
    url(r'^vendor/item/(?P<code>\w+?)/price$', 'item_update_price', name='item_update_price'),
    url(r'^vendor/item/(?P<code>\w+?)/name$', 'item_update_name', name='item_update_name'),
    url(r'^vendor/item/(?P<code>\w+?)/type$', 'item_update_type', name='item_update_type'),
    url(r'^vendor/item/(?P<code>\w+?)/to_print$', 'item_to_print', name='item_to_print'),

    url(r'^login/?$', 'login_view', name='login_view'),
    url(r'^logout/?$', 'logout_view', name='logout_view'),

    url(r'^api/', include('kirppu.app.checkout.urls')),
)
