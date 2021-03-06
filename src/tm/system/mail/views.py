# Pyramid
from pyramid.renderers import render
from pyramid.response import Response

import premailer



# @simple_route("/sample-html-email", route_name="sample_html_email")
def sample_html_email(request):
    """Render a sample of HTML email.

    This view is conditionally enabled for development sites.
    """

    html_body = render("email/sample.html", {}, request=request)
    html_body = premailer.transform(html_body)

    return Response(html_body)
