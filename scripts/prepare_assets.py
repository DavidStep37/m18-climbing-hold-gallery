#!/usr/bin/env python3
"""Create isolated PNGs from user-supplied, appropriately licensed photos.

Input files: <input-dir>/<hold-id>.jpg|jpeg|png|webp. Products photographed
against a pale, near-neutral backdrop work best; multi-hold set photos require
manual cropping first. No photos are fetched, bundled or redistributed.
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[1]

def prepare(src: Path, dest: Path):
    with Image.open(src) as original:
        image = original.convert('RGBA')
    image.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
    rgba = np.asarray(image).astype(np.int16)
    rgb = rgba[:, :, :3]
    if rgba[:, :, 3].min() < 250:
        # Honor genuinely transparent, user-supplied PNGs as-is.
        mask = rgba[:, :, 3] > 4
    else:
        mx, mn = rgb.max(axis=2), rgb.min(axis=2)
        colorful = (mx - mn > 29) & (mx > 65) & (mn < 225) & (rgb.sum(axis=2) < 715)
        colorful = ndi.binary_opening(colorful, iterations=2)
        labels, _ = ndi.label(colorful)
        areas = np.bincount(labels.ravel()); areas[0] = 0
        if not areas.max():
            raise ValueError(f'No colorful foreground found in {src.name}; crop/remove background manually.')
        mask = labels == areas.argmax()
    mask = ndi.binary_closing(mask, iterations=7)
    mask = ndi.binary_fill_holes(mask)
    mask = ndi.binary_dilation(mask, iterations=4)
    alpha = (image.getchannel('A') if rgba[:, :, 3].min() < 250
             else Image.fromarray((mask.astype('uint8') * 255), 'L').filter(ImageFilter.GaussianBlur(1.3)))
    photo = image.copy(); photo.putalpha(alpha)
    crop = photo.crop(alpha.getbbox())
    crop.thumbnail((420, 420), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
    canvas.alpha_composite(crop, ((512-crop.width)//2, (512-crop.height)//2))
    canvas.save(dest)
    black = Image.new('RGBA', (512, 512), 'black'); black.alpha_composite(canvas)
    black.convert('RGB').resize((256, 256), Image.Resampling.LANCZOS).save(dest.with_name(dest.stem + '-key.png'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True, help='folder containing <hold-id>.jpg/png/webp photos')
    args = parser.parse_args()
    holds = json.loads((ROOT/'gallery.json').read_text())
    out = ROOT/'assets'; out.mkdir(exist_ok=True)
    for hold in holds:
        ident = hold['id']
        choices = [args.input_dir/f'{ident}.{ext}' for ext in ('png','jpg','jpeg','webp')]
        source = next((p for p in choices if p.is_file()), None)
        if source is None:
            raise SystemExit(f'Missing photo for {ident}: supply {ident}.jpg/png/webp in {args.input_dir}')
        prepare(source, out/f'{ident}.png')
        print(f'{ident}: {source.name} -> assets/{ident}.png, assets/{ident}-key.png')

if __name__ == '__main__': main()
