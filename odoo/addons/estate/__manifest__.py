{
    'name': "Real Estate Module",
    'version': '1.0',
    'depends': ['base', 'web'],
    'author': "Rares Tamaian",
    'category': 'Category',
    'description': """
    Real Estate Custom Module
    """,
    'assets': {
        'web.assets_backend': [
            'estate/static/css/custom_styles.css',
            'estate/static/js/custom_pagination.js',
        ],
    },
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
        'views/estate_type_views.xml',
        'views/estate_tag_views.xml',
        'views/estate_offer_views.xml',
        'views/estate_menus.xml',
        'views/list_view.xml',
        'views/form_view.xml',
        'views/kanban_view.xml',
        'views/search_view.xml',
        'views/offer_list_view.xml',
        'views/property_tag_list_view.xml',
        'views/property_tag_form_view.xml',
        'views/property_type_form_view.xml',
        'views/property_type_list_view.xml',
        'report/estate_property_templates.xml',
        'report/estate_property_reports.xml',
        'data/estate_cron.xml',
        'views/estate_user_form_view_inherit.xml',
    ],
    # data files containing optionally loaded demonstration data
    'demo': [
        # 'demo/demo_data.xml',
    ],
    'installable': True,  # module can be installed by the user through the interface
    'application': True,  # module is seen as an app in the search bar
}