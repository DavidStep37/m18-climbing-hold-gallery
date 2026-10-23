import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]

def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

class PipelineTests(unittest.TestCase):
    def test_cutout_isolated_and_uniform(self):
        with TemporaryDirectory() as temp:
            base=Path(temp)
            photo=Image.new('RGB',(600,600),'#f6f6f6')
            ImageDraw.Draw(photo).ellipse((130,160,480,430),fill='#1e9ccf')
            source=base/'sample.jpg';photo.save(source)
            module('prepare_assets').prepare(source,base/'hold.png')
            rgba=Image.open(base/'hold.png')
            key=Image.open(base/'hold-key.png')
            self.assertEqual((512,512),rgba.size)
            self.assertEqual((0,0,0,0),rgba.getpixel((0,0)))
            self.assertEqual((256,256),key.size)
            self.assertEqual((0,0,0),key.getpixel((0,0)))

    def test_existing_scene_refused(self):
        installer=module('install_scene')
        with TemporaryDirectory() as temp:
            base=Path(temp)/'existing.sdProfile';base.mkdir()
            path=base/'manifest.json'
            data={'DeviceUUID':'M18V25E','Name':'岩点陈列柜','Actions':{'0,0':{'UUID':'user.action'}}}
            path.write_text(json.dumps(data))
            matched=installer.choose_profile('岩点陈列柜',base)
            self.assertEqual(matched[0],path)
            self.assertTrue(matched[1]['Actions'])

    def test_assets_not_staged(self):
        names={a['id'] for a in json.loads((ROOT/'gallery.json').read_text())}
        self.assertEqual(15,len(names))
        self.assertEqual(names,{a['id'] for a in json.loads((ROOT/'photo-references.json').read_text())})

if __name__=='__main__':unittest.main()
