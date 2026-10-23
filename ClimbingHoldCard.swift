import AppKit
import QuartzCore

private struct Hold: Decodable {
    let id: String
    let name: String
}

private let holds: [Hold] = {
    guard let url = Bundle.main.url(forResource: "gallery", withExtension: "json"),
          let data = try? Data(contentsOf: url),
          let decoded = try? JSONDecoder().decode([Hold].self, from: data) else { return [] }
    return decoded
}()

// A plain view avoids NSButtonCell's built-in pressed-image offset.
// Its click gesture changes selection only; size animation is centered by CardApp.
final class HoldThumbnail: NSView {
    let index: Int
    var onSelect: ((Int) -> Void)?
    private let artwork = NSImageView()

    init(frame: NSRect, index: Int, name: String, image: NSImage?) {
        self.index = index
        super.init(frame: frame)
        artwork.frame = bounds
        artwork.autoresizingMask = [.width, .height]
        artwork.image = image
        artwork.imageScaling = .scaleProportionallyUpOrDown
        // Layer scale never changes the view frame or NSImageView layout. Keeping
        // the view geometry fixed prevents the transient "jump then settle".
        wantsLayer = true
        addSubview(artwork)
        addGestureRecognizer(NSClickGestureRecognizer(target: self, action: #selector(clicked)))
        toolTip = name
        setAccessibilityRole(.button)
        setAccessibilityLabel(name)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    @objc private func clicked() { onSelect?(index) }
}

final class CardWindow: NSWindow {
    override var canBecomeKey: Bool { true }
}

final class CardApp: NSObject, NSApplicationDelegate {
    private var window: CardWindow!
    private let imageView = NSImageView()
    private let label = NSTextField(labelWithString: "")
    private var thumbnails: [HoldThumbnail] = []
    private var thumbnailStrip: NSScrollView!
    private let thumbnailWidth: CGFloat = 60
    private let thumbnailStep: CGFloat = 72
    private var selectedIndex = -1
    private var transitionID = 0
    private var keyboardMonitor: Any?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        let screen = NSScreen.main?.visibleFrame ?? NSRect(x: 0, y: 0, width: 1280, height: 800)
        let w: CGFloat = 520, h: CGFloat = 680
        window = CardWindow(contentRect: NSRect(x: screen.midX - w/2, y: screen.midY - h/2, width: w, height: h),
                            styleMask: [.borderless], backing: .buffered, defer: false)
        window.backgroundColor = .clear
        window.isOpaque = false
        window.hasShadow = true
        window.level = .floating
        window.collectionBehavior = [.moveToActiveSpace, .fullScreenAuxiliary]
        let root = NSView(frame: NSRect(x: 0, y: 0, width: w, height: h))
        root.wantsLayer = true
        root.layer?.backgroundColor = NSColor.black.cgColor
        root.layer?.cornerRadius = 24
        root.layer?.masksToBounds = true
        root.layer?.borderWidth = 1
        root.layer?.borderColor = NSColor(white: 1, alpha: 0.11).cgColor
        window.contentView = root

        imageView.frame = NSRect(x: 86, y: 298, width: 348, height: 320)
        imageView.imageScaling = .scaleProportionallyUpOrDown
        root.addSubview(imageView)

        label.frame = NSRect(x: 58, y: 233, width: 404, height: 52)
        label.alignment = .center
        label.font = NSFont.systemFont(ofSize: 32, weight: .medium)
        label.textColor = NSColor(white: 0.72, alpha: 1)
        label.maximumNumberOfLines = 1
        root.addSubview(label)

        addControl("×", frame: NSRect(x: 465, y: 617, width: 40, height: 40), action: #selector(closeCard), fontSize: 29, to: root)
        addControl("‹", frame: NSRect(x: 16, y: 407, width: 50, height: 64), action: #selector(previous), fontSize: 48, to: root)
        addControl("›", frame: NSRect(x: 454, y: 407, width: 50, height: 64), action: #selector(next), fontSize: 48, to: root)

        // Single, borderless filmstrip. Extra transparent space lets the first and last
        // hold occupy the exact center, just like every hold in the middle.
        let stripFrame = NSRect(x: 48, y: 42, width: 424, height: 112)
        thumbnailStrip = NSScrollView(frame: stripFrame)
        thumbnailStrip.drawsBackground = false
        thumbnailStrip.hasHorizontalScroller = false
        thumbnailStrip.hasVerticalScroller = false
        thumbnailStrip.horizontalScrollElasticity = .none
        thumbnailStrip.verticalScrollElasticity = .none
        thumbnailStrip.contentView.drawsBackground = false
        thumbnailStrip.wantsLayer = true
        let fade = CAGradientLayer()
        fade.frame = NSRect(origin: .zero, size: stripFrame.size)
        fade.startPoint = CGPoint(x: 0, y: 0.5)
        fade.endPoint = CGPoint(x: 1, y: 0.5)
        fade.colors = [NSColor.clear.cgColor, NSColor.black.cgColor,
                       NSColor.black.cgColor, NSColor.clear.cgColor]
        fade.locations = [0, 0.13, 0.87, 1]
        thumbnailStrip.layer?.mask = fade

        let leadingSpace = (stripFrame.width - thumbnailWidth) / 2
        let documentWidth = 2 * leadingSpace + thumbnailWidth + CGFloat(holds.count - 1) * thumbnailStep
        let document = NSView(frame: NSRect(x: 0, y: 0, width: documentWidth, height: stripFrame.height))
        for (index, hold) in holds.enumerated() {
            let button = HoldThumbnail(frame: NSRect(x: leadingSpace + CGFloat(index) * thumbnailStep,
                                                     y: 25, width: thumbnailWidth, height: 66),
                                       index: index, name: hold.name, image: image(for: hold.id))
            button.onSelect = { [weak self] selected in self?.select(selected) }
            document.addSubview(button)
            thumbnails.append(button)
        }
        thumbnailStrip.documentView = document
        root.addSubview(thumbnailStrip)
        keyboardMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self, self.window.isVisible, self.window.isKeyWindow else { return event }
            switch event.keyCode {
            case 53: self.closeCard(); return nil // Esc
            case 123: self.move(by: -1); return nil // left
            case 124: self.move(by: 1); return nil // right
            default: return event
            }
        }
        show(CommandLine.arguments.dropFirst().first ?? "sloper")
    }

    private func addControl(_ title: String, frame: NSRect, action: Selector, fontSize: CGFloat, to view: NSView) {
        let button = NSButton(frame: frame)
        button.title = title
        button.isBordered = false
        button.font = NSFont.systemFont(ofSize: fontSize, weight: .ultraLight)
        button.contentTintColor = NSColor(white: 1, alpha: 0.66)
        button.target = self
        button.action = action
        view.addSubview(button)
    }

    private func image(for id: String) -> NSImage? {
        guard let url = Bundle.main.url(forResource: id, withExtension: "png", subdirectory: "icons") else { return nil }
        return NSImage(contentsOf: url)
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        guard let url = urls.first, url.scheme?.lowercased() == "climbhold" else { return }
        let id = (url.host ?? url.path.replacingOccurrences(of: "/", with: "")).lowercased()
        show(id)
    }

    func show(_ id: String) {
        guard let index = holds.firstIndex(where: { $0.id == id }) else { return }
        select(index)
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func select(_ index: Int) {
        guard holds.indices.contains(index) else { return }
        let animated = window.isVisible && selectedIndex != index
        selectedIndex = index
        transitionID += 1
        let currentTransition = transitionID
        let hold = holds[index]

        // Fade the large image and word as one visual unit. Superseded transitions
        // never replace the newest selection when the user navigates rapidly.
        if animated {
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.15
                context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
                imageView.animator().alphaValue = 0
                label.animator().alphaValue = 0
            } completionHandler: { [weak self] in
                guard let self, self.transitionID == currentTransition else { return }
                self.imageView.image = self.image(for: hold.id)
                self.label.stringValue = hold.name
                NSAnimationContext.runAnimationGroup { context in
                    context.duration = 0.29
                    context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
                    self.imageView.animator().alphaValue = 1
                    self.label.animator().alphaValue = 1
                }
            }
        } else {
            imageView.image = image(for: hold.id)
            label.stringValue = hold.name
            imageView.alphaValue = 1
            label.alphaValue = 1
        }

        // The thumbnail frames NEVER move or resize. A centered CALayer transform
        // is the only scale effect. In particular, NSImageView's autoresizing
        // cannot briefly shift its bitmap when a click starts an animation.
        for (n, thumbnail) in thumbnails.enumerated() {
            guard let layer = thumbnail.layer else { continue }
            let scale: CGFloat = n == index ? 1.20 : 1.0
            let opacity: Float = n == index ? 1 : 0.32
            let fromScale = (layer.presentation()?.value(forKeyPath: "transform.scale") as? NSNumber)?.doubleValue
                ?? (layer.value(forKeyPath: "transform.scale") as? NSNumber)?.doubleValue
                ?? 1.0
            let fromOpacity = layer.presentation()?.opacity ?? layer.opacity

            CATransaction.begin()
            CATransaction.setDisableActions(true)
            layer.transform = CATransform3DMakeScale(scale, scale, 1)
            layer.opacity = opacity
            CATransaction.commit()

            guard animated else { continue }
            let scaleAnimation = CABasicAnimation(keyPath: "transform.scale")
            scaleAnimation.fromValue = fromScale
            scaleAnimation.toValue = scale
            scaleAnimation.duration = 0.36
            scaleAnimation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            layer.add(scaleAnimation, forKey: "selectionScale")

            let fadeAnimation = CABasicAnimation(keyPath: "opacity")
            fadeAnimation.fromValue = fromOpacity
            fadeAnimation.toValue = opacity
            fadeAnimation.duration = 0.30
            fadeAnimation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            layer.add(fadeAnimation, forKey: "selectionOpacity")
        }
        // Scroll in X only. Preserve the clip view's existing Y to avoid an
        // implicit vertical scroll/correction during AppKit's animation cycle.
        let currentY = thumbnailStrip.contentView.bounds.origin.y
        NSAnimationContext.runAnimationGroup { context in
            context.duration = animated ? 0.40 : 0
            context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
            thumbnailStrip.contentView.animator().setBoundsOrigin(
                NSPoint(x: CGFloat(index) * thumbnailStep, y: currentY))
        }

    }

    private func move(by amount: Int) {
        select((selectedIndex + amount + holds.count) % holds.count)
    }

    @objc private func previous() { move(by: -1) }
    @objc private func next() { move(by: 1) }
    @objc private func closeCard() { window.orderOut(nil) }
    func applicationWillTerminate(_ notification: Notification) {
        if let keyboardMonitor { NSEvent.removeMonitor(keyboardMonitor) }
    }
}

let app = NSApplication.shared
let delegate = CardApp()
app.delegate = delegate
app.run()
