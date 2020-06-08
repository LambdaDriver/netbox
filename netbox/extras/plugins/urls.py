import logging
from django.apps import apps
from django.conf import settings
from django.conf.urls import include
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.utils.module_loading import import_string

from . import views

# Initialize URL base, API, and admin URL patterns for plugins
plugin_patterns = []
plugin_api_patterns = [
    path('', views.PluginsAPIRootView.as_view(), name='api-root'),
    path('installed-plugins/', views.InstalledPluginsAPIView.as_view(), name='plugins-list')
]
plugin_admin_patterns = [
    path('installed-plugins/', staff_member_required(views.InstalledPluginsAdminView.as_view()), name='plugins_list')
]

# Register base/API URL patterns for each plugin
for plugin_path in settings.PLUGINS:
    logging.info(f'Initializing Plugin Path: {plugin_path}')
    plugin_name = plugin_path.split('.')[-1]
    logging.debug(f'Resolved Plugin Name: {plugin_path}')
    app = apps.get_app_config(plugin_name)
    base_url = getattr(app, 'base_url') or app.label
    logging.info(f'Base URL is: {base_url}')

    # Check if the plugin specifies any base URLs
    try:
        urlpatterns_path = f"{plugin_path}.urls.urlpatterns"
        logging.debug(f'Attempting to load URL patterns from: {urlpatterns_path}')
        urlpatterns = import_string(urlpatterns_path)
        logging.debug(f'Attempting to register URLs from: {urlpatterns_path}')
        plugin_patterns.append(
            path(f"{base_url}/", include((urlpatterns, app.label)))
        )
        logging.debug(f'Successfully registered URLs from: {urlpatterns_path}')
    except ImportError:
        logging.exception(f'Could not load URLs for: {base_url}')

    # Check if the plugin specifies any API URLs
    try:
        urlpatterns = import_string(f"{plugin_path}.api.urls.urlpatterns")
        plugin_api_patterns.append(
            path(f"{base_url}/", include((urlpatterns, f"{app.label}-api")))
        )
    except ImportError:
        logging.exception(f'Could not load API URLs for: {base_url}')
    
    logging.info(f'Initializion complete for: {plugin_path}')