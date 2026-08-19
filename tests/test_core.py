import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT))

import platform_utils
import omni_cli
from favicon_manager import sanitize_svg

spec=importlib.util.spec_from_file_location('omni_install',ROOT/'install.py')
install=importlib.util.module_from_spec(spec);spec.loader.exec_module(install)

class CoreTests(unittest.TestCase):
    def test_version_and_manifest_match(self):
        v=(ROOT/'VERSION').read_text().strip()
        manifest=json.loads((ROOT/'manifest.json').read_text())
        self.assertEqual(v,manifest['version'])
        self.assertEqual(v,'4.0.0')

    def test_sources_are_pinned_and_unique(self):
        cfg=json.loads((ROOT/'sources.json').read_text())
        ids=[]
        for group in ('archives','files'):
            for s in cfg[group]:
                ids.append(s['id']);self.assertTrue(s['urls']);self.assertIn('https://',s['urls'][0])
                for url in s['urls']:
                    # Only the documented Material source is intentionally floating.
                    if s['source']!='material': self.assertNotIn('/heads/',url)
        self.assertEqual(len(ids),len(set(ids)))

    def test_figma_manifest_localhost_only(self):
        m=json.loads((ROOT/'figma-plugin'/'manifest.json').read_text())
        domains=m['networkAccess']['allowedDomains']
        self.assertEqual(domains,['http://localhost:17836'])
        self.assertNotIn('127.0.0.1',json.dumps(m))

    def test_svg_sanitizer_removes_script_and_remote_href(self):
        raw=b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><image href="https://evil.test/a.png"/><path d="M0 0h1v1z"/></svg>'
        clean=sanitize_svg(raw).decode()
        self.assertNotIn('script',clean.lower())
        self.assertNotIn('evil.test',clean)
        self.assertIn('path',clean)

    def test_zip_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);z=td/'bad.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('../escape.txt','bad')
            with self.assertRaises(RuntimeError):install.extract_archive(z,td/'out','zip')

    def test_cli_brand_filter_includes_favicons(self):
        items=[
            {'id':'a','name':'github','label':'GitHub','kind':'brand','source':'simpleicons'},
            {'id':'b','name':'github.com','label':'github.com','kind':'favicon','source':'favicons'},
            {'id':'c','name':'camera','label':'Camera','kind':'ui','source':'tabler'},
        ]
        xs=omni_cli.search(items,'github','kind:brand',20)
        self.assertEqual({x['id'] for x in xs},{'a','b'})

    def test_platform_url_is_localhost(self):
        self.assertEqual(platform_utils.app_url(17836),'http://localhost:17836')

if __name__=='__main__':unittest.main()
