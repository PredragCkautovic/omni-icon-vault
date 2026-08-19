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
        self.assertEqual(v,'4.1.1')

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

    def test_svg_sanitizer_keeps_safe_presentation_style(self):
        raw=b'<svg xmlns="http://www.w3.org/2000/svg"><path style="fill:#663399;stroke:none" d="M0 0h1v1z"/></svg>'
        clean=sanitize_svg(raw).decode()
        self.assertIn('fill:#663399',clean)

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

    def test_cli_format_filter_and_sort(self):
        items=[
            {'id':'b','name':'beta','label':'Beta','kind':'ui','source':'tabler','sourceLabel':'Tabler','char':'x'},
            {'id':'a','name':'alpha','label':'Alpha','kind':'ui','source':'lucide','sourceLabel':'Lucide','svg':'<svg/>'},
        ]
        xs=omni_cli.search(items,'','all',20,'svg','name')
        self.assertEqual([x['id'] for x in xs],['a'])

    def test_macos_bundle_version_is_dynamic(self):
        text=(ROOT/'install.py').read_text('utf-8')
        self.assertIn('CFBundleVersion</key><string>{version()}</string>',text)

    def test_platform_url_is_localhost(self):
        self.assertEqual(platform_utils.app_url(17836),'http://localhost:17836')

    def test_browser_is_api_driven(self):
        html=(ROOT/'browser'/'index.html').read_text('utf-8')
        js=(ROOT/'browser'/'app.js').read_text('utf-8')
        self.assertNotIn('icon-data.js',html)
        self.assertIn('/api/search',js)
        self.assertIn('/api/stats',js)

    def test_browser_javascript_ids_exist_in_html(self):
        import re
        html=(ROOT/'browser'/'index.html').read_text('utf-8')
        js=(ROOT/'browser'/'app.js').read_text('utf-8')
        refs=set(re.findall(r"\$\('#([A-Za-z0-9_-]+)'\)",js))
        ids=set(re.findall(r'id="([A-Za-z0-9_-]+)"',html))
        self.assertFalse(refs-ids, f'missing browser element ids: {sorted(refs-ids)}')

    def test_server_search_pagination_format_and_stats(self):
        from omni_server import IconStore
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);(td/'browser').mkdir()
            items=[
                {'id':'a','source':'tabler','sourceLabel':'Tabler','kind':'ui','name':'camera','label':'Camera','style':'outline','svg':'<svg/>'},
                {'id':'b','source':'material','sourceLabel':'Material','kind':'ui','name':'camera','label':'Camera Material','style':'outlined','char':'x'},
                {'id':'c','source':'simpleicons','sourceLabel':'Simple Icons','kind':'brand','name':'github','label':'GitHub','style':'brand','svg':'<svg/>'},
            ]
            (td/'browser'/'icon-data.json').write_text(json.dumps(items))
            (td/'browser'/'source-meta.json').write_text(json.dumps([{'source':'tabler','label':'Tabler','kind':'ui','count':1}]))
            store=IconStore(td)
            page,total=store.search('camera','all','svg','name',0,1)
            self.assertEqual(total,1);self.assertEqual(page[0]['id'],'a')
            self.assertEqual(store.stats['formats']['svg'],2)
            self.assertEqual(store.stats['formats']['font'],1)

    def test_custom_svg_index_uses_sanitizer(self):
        text=(ROOT/'tools'/'build-index.py').read_text('utf-8')
        self.assertIn('read_svg(p, sanitize=True)',text)

    def test_tar_gz_archive_supported(self):
        import tarfile
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); src=td/'src'; src.mkdir(); (src/'ok.txt').write_text('ok')
            arc=td/'sample.tgz'
            with tarfile.open(arc,'w:gz') as tf: tf.add(src/'ok.txt',arcname='package/ok.txt')
            out=td/'out'; install.extract_archive(arc,out,'tar.gz')
            self.assertEqual((out/'ok.txt').read_text(),'ok')

    def test_phosphor_uses_pinned_npm_tarball(self):
        cfg=json.loads((ROOT/'sources.json').read_text())
        phosphor=next(x for x in cfg['archives'] if x['id']=='phosphor')
        self.assertEqual(phosphor['version'],'2.1.1')
        self.assertEqual(phosphor['type'],'tar.gz')
        self.assertIn('registry.npmjs.org/@phosphor-icons/core/-/core-2.1.1.tgz',phosphor['urls'][0])

    def test_bootstrap_parser_has_svg_fallback(self):
        text=(ROOT/'tools'/'build-index.py').read_text('utf-8')
        self.assertIn("for candidate in ('bootstrap-icons.json','bootstrapicons.json')",text)
        self.assertIn("for svg_path in sorted(icon_root.glob('*.svg'))",text)

    def test_installer_self_heals_required_source_cache(self):
        text=(ROOT/'install.py').read_text('utf-8')
        self.assertIn('reset_source_assets(affected)',text)
        self.assertIn('only_sources=affected',text)

if __name__=='__main__':unittest.main()
