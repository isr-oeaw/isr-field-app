from django.conf import settings


def branding_template_context():
    """Brand name + CSS theme variables for templates and render_to_string (no Request)."""
    return {
        'site_brand_name': settings.SITE_NAME,
        'theme_primary': settings.THEME_PRIMARY,
        'theme_secondary': settings.THEME_SECONDARY,
        'theme_accent': settings.THEME_ACCENT,
        'theme_primary_light': settings.THEME_PRIMARY_LIGHT,
        'theme_primary_dark': settings.THEME_PRIMARY_DARK,
    }


def branding(request):
    return branding_template_context()
