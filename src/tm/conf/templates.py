def includeme(config):
    # Jinja 2 templates as .html files
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.css')
    config.add_jinja2_renderer('.xml')
