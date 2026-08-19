import importlib.util,tempfile,unittest,zipfile,re,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_builder',ROOT/'scripts'/'build_release.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReleaseTests(unittest.TestCase):
    def test_release_does_not_bundle_vendor_or_cache(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'x.zip';m.build_zip(out,'linux',False)
            names=zipfile.ZipFile(out).namelist()
            self.assertFalse(any('/vendor/' in x and not x.endswith('/vendor/') for x in names))
            self.assertFalse(any('/cache/' in x and not x.endswith('/cache/') for x in names))
            self.assertTrue(any(x.endswith('/INSTALL_LINUX.sh') for x in names))
            self.assertEqual(len(names),len(set(names)))

    def test_readme_assets_exist_and_svg_assets_parse(self):
        readme=(ROOT/'README.md').read_text('utf-8')
        refs=re.findall(r'src="(docs/assets/[^"]+)"',readme)
        self.assertTrue(refs)
        for ref in refs:
            path=ROOT/ref
            self.assertTrue(path.exists(),ref)
            if path.suffix=='.svg': ET.parse(path)

    def test_flagship_release_assets_are_packaged(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'source.zip';m.build_zip(out,'source',True)
            names=zipfile.ZipFile(out).namelist()
            self.assertTrue(any(x.endswith('/docs/assets/omni-4.2-showcase.svg') for x in names))
            self.assertTrue(any(x.endswith('/docs/assets/omni-4.2-bento.svg') for x in names))
            self.assertFalse(any(x.endswith('/browser/icon-data.json') for x in names))

    def test_source_includes_github_workflows(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'source.zip';m.build_zip(out,'source',True)
            names=zipfile.ZipFile(out).namelist()
            self.assertTrue(any('/.github/workflows/' in x for x in names))
if __name__=='__main__':unittest.main()
