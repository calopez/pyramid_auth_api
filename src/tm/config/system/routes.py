from pyramid.response import Response

def my_view(request):
    return { 'user': { 'friendly_name': 'Carlos Andres Lopez'}}
def home(request):
    return Response('''
    <div style="margin: 200px">
        <form action="login/facebook" method="POST">
            <input type="submit" value="Authenticate With Facebook">
        </form>
    </div>
    ''')

def includeme(config):
    from tm.system.user import subscribers
    from tm.system.user import api

    config.add_route('home', '/')
    config.add_view(home, route_name='home')

    config.add_route('email_sample', '/email-sample', accept='application/json')
    config.add_view(my_view,
                    permission='authenticated',
                    route_name='email_sample',
                    renderer="tm.system.user:templates/login/email/forgot_password.body.html")

    config.add_route('users', '/users', accept='application/json')

    config.add_route('login', '/login', accept='application/json')
    config.add_route('logout', '/logout', accept='application/json')
    config.add_route('forgot_password', '/forgot-password', accept='application/json')
    config.add_route('reset_password', '/reset-password/{code}', accept='application/json')
    config.add_route('signup', '/signup', accept='application/json')
    config.add_route('activate', '/activate/{code}', accept='application/json')
    config.scan(subscribers)
    config.scan(api)