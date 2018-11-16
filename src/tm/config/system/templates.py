def includeme(config):
    # Jinja 2 templates as .html files
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.css')
    config.add_jinja2_renderer('.xml')

    config.include("tm.system.core.templatecontext")
    config.include("tm.system.core.vars")

     # Add core templates to the search path
    config.add_jinja2_search_path('tm.system.core:templates', name='.html')
    config.add_jinja2_search_path('tm.system.core:templates', name='.txt')
    config.add_jinja2_search_path('tm.system.core:templates', name='.xml')
    config.add_jinja2_search_path('tm.system.core:templates', name='.css')

    # Add user templates to the search path
    config.add_jinja2_search_path('tm.system.user:templates', name='.html')
    config.add_jinja2_search_path('tm.system.user:templates', name='.txt')