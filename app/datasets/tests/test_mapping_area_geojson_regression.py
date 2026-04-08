"""
Layer 1 regression tests: mapping-area GeoJSON import wiring in template + static JS.

These catch accidental removal of controls or parser entry points (e.g. merge conflicts)
without executing browser JavaScript.
"""

import os

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import DataSet


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class MappingAreaGeojsonRegressionTests(TestCase):
    """Ensure data-input exposes mapping-area GeoJSON import UI and script hooks."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.collaborator = User.objects.create_user(username='collab', password='pass')
        self.dataset = DataSet.objects.create(
            name='Regression Dataset',
            owner=self.owner,
            enable_mapping_areas=True,
        )
        self.dataset.shared_with.add(self.collaborator)
        self.url = reverse('dataset_data_input', kwargs={'dataset_id': self.dataset.id})

    def _read_data_input_js(self):
        js_file_path = os.path.join(settings.STATIC_ROOT, 'js', 'data-input.js')
        if not os.path.exists(js_file_path):
            js_file_path = os.path.join(settings.STATICFILES_DIRS[0], 'js', 'data-input.js')
        self.assertTrue(os.path.exists(js_file_path), f'data-input.js not found at {js_file_path}')
        with open(js_file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_owner_sees_geojson_import_controls_when_mapping_areas_enabled(self):
        client = Client()
        client.force_login(self.owner)
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="importGeojsonBtn"', content)
        self.assertIn('id="importMappingAreaGeojsonInput"', content)
        self.assertIn('Import GeoJSON', content)
        self.assertNotIn('onclick="triggerImportMappingAreaGeojson()', content)

    def test_collaborator_does_not_see_geojson_import_controls(self):
        client = Client()
        client.force_login(self.collaborator)
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('id="importMappingAreaGeojsonInput"', content)
        self.assertNotIn('id="importGeojsonBtn"', content)

    def test_mapping_areas_disabled_hides_import_controls(self):
        self.dataset.enable_mapping_areas = False
        self.dataset.save(update_fields=['enable_mapping_areas'])
        client = Client()
        client.force_login(self.owner)
        response = client.get(self.url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('id="importMappingAreaGeojsonInput"', content)

    def test_data_input_js_contains_mapping_area_geojson_wiring(self):
        js = self._read_data_input_js()
        markers = [
            'function triggerImportMappingAreaGeojson',
            'window.triggerImportMappingAreaGeojson = triggerImportMappingAreaGeojson',
            'function onMappingAreaGeojsonFileSelected',
            'function extractMappingAreaGeometryFromGeojson',
            'function geometryFromGeojsonFragment',
            'importMappingAreaGeojsonInput',
            "importGeojsonBtn.addEventListener('click'",
            "geoInput.addEventListener('change', onMappingAreaGeojsonFileSelected)",
        ]
        for needle in markers:
            self.assertIn(needle, js, f'Expected data-input.js to contain: {needle!r}')
