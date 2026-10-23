# M18 Climbing Hold Gallery · 岩点陈列柜

Turn the **15 LCD keys** of a Mirabox / StreamDock M18 into a small climbing-hold display. Each key shows a single hold on black. Press a physical key to open a minimal rounded macOS card with a larger photo and English name. Navigate with the left/right arrows or keyboard, click the one-line fading thumbnail strip, and close with × or Esc.

> **Status:** Tested locally on **M18V3 E / USB `6603:1012`**, macOS on Apple Silicon, with the official StreamDock app. Other M18 revisions, other vendor IDs and Windows/Linux are **not confirmed**. A user must verify the final physical-key press on their own device.
>
> **Photos are not included.** Code is MIT-licensed; product photos are not. Supply images you own or have permission to use. The optional [`photo-references.json`](photo-references.json) identifies the Escape Climbing product pages used in the personal prototype; it does **not** grant a license or provide downloads. Do not redistribute those images without permission.

## What you need

- macOS with Xcode Command Line Tools (`xcode-select --install`, if not already present), Python 3, and the official StreamDock application.
- An M18 recognized by StreamDock. The installer checks that the profile reports device UUID `M18V25E` and deliberately refuses other variants until verified.
- 15 appropriately licensed individual-hold photos on a light, neutral background. One photo per ID in [`gallery.json`](gallery.json). PNG/JPEG/WebP work. The supplied segmentation works best for colorful single holds; manually crop multi-hold or low-contrast photos first.

## Set up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

1. Put your photos in a local folder (example: `~/Pictures/my-holds/`) named `sloper.jpg`, `crimp.jpg`, `hueco.jpg`, etc. Use the **ID**, not the visible name, from `gallery.json`. `photo-references.json` is only a provenance aid; obtaining rights to photos is your responsibility.
2. Prepare photos and build the app:

   ```bash
   python3 scripts/prepare_assets.py --input-dir "$HOME/Pictures/my-holds"
   python3 scripts/build.py
   ```

   This creates transparent `assets/<id>.png`, 256×256 black key images `assets/<id>-key.png`, and locally ad-hoc-signed apps under `dist/`. Everything stays on your machine; `assets/`, `dist/` and backups are gitignored. Review the cutouts before installation—automatic masking may need manual correction.

3. In **StreamDock**, create a **new empty scene** named `岩点陈列柜` on your M18. Keep your existing scenes intact. **Quit StreamDock completely** (not just closing its window), then install:

   ```bash
   python3 scripts/install_scene.py
   open -a "$PWD/dist/ClimbingHoldCard.app"   # registers the local climbhold:// URL scheme
   open -a /Applications/StreamDock.app
   ```

   The installer looks for exactly one scene with the right name and `M18V25E`, checks that it is empty, backs up its manifest, and installs the 15 built-in **Open** actions. It never writes to another scene. If automatic discovery is ambiguous, supply `--profile "/absolute/path/to/your-scene.sdProfile"`. The three non-LCD bottom keys are left alone. **Do not move or rename this project directory after installation**: StreamDock stores absolute paths to `dist/launchers/*.app`.

4. Select the new scene in StreamDock and press a **physical** key. A card for the corresponding hold should appear. To change the gallery labels/order, edit `gallery.json`, rebuild, and install into a *fresh empty scene*. The code does not silently replace a populated scene.

## Interaction and design

- Round black card; large real photo and subdued English label; no brand/model size prefixes on the card.
- The arrows are beside the large photo. Large photo and label cross-fade; the strip scrolls smoothly along X.
- One borderless thumbnail row fades into the edges. The focused hold is centered and enlarged around a **fixed horizontal centerline** using a layer transform, not a changing frame. Other thumbnails are dimmed. There is no native button press displacement.
- Esc or × hides the card; a later key press opens it again.

## Files

| Path | Purpose |
|---|---|
| `ClimbingHoldCard.swift` | Native macOS card UI, carousel, keyboard/click navigation |
| `HoldLauncher.swift` | Small per-key launcher for StreamDock's Open action |
| `gallery.json` | 15 safe IDs and display names; no photo data |
| `scripts/prepare_assets.py` | Convert your licensed photos to consistent transparent + black canvases |
| `scripts/build.py` | Compile and locally sign the card + launchers |
| `scripts/install_scene.py` | Locate a new empty M18 scene, back it up, install actions |
| `photo-references.json` | External product-page attribution (not a photo license) |

## Scope, safety and rights

The [MIT license](LICENSE) applies to **code and documentation only**, not third-party imagery. This repository intentionally contains **no vendor photo binaries, derived photo PNGs, exported StreamDock profiles, machine-specific backup files, or device serials**. The builder produces local ad-hoc signatures rather than an official signed/notarized release. The scene installer edits the official application's local JSON profile while the app is quit; back up other important StreamDock data independently before trying a new tool. StreamDock and Escape Climbing are third parties; this is an independent community experiment, not an official plugin or endorsement.

If a physical press does nothing, confirm the gallery scene is selected, the launcher path in the key's Open action exists, and the card app has been launched once (`open -a "$PWD/dist/ClimbingHoldCard.app"`). You can restore the scene from the installer-generated JSON in `backups/` after quitting StreamDock.

---

## 中文速览

这是针对 M18V3 E 的个人原型公开版。仓库只发布 MIT 代码，不附带厂商照片或处理后的岩点图片。你需要自己准备有使用权的 15 张单个岩点照片，按 `gallery.json` 的 ID 命名并运行上方命令。安装脚本只接受**预先在 StreamDock 中创建的空白「岩点陈列柜」场景**，会备份配置并拒绝覆盖已有动作；安装后保持项目目录位置不变。其他 M18 硬件版本尚未验证。
