import AppKit

// Each tiny launcher is an independent target for StreamDock's built-in Open action.
// The shared card app owns the window and switches the currently shown hold.
let hold = Bundle.main.object(forInfoDictionaryKey: "ClimbingHoldID") as? String ?? "sloper"
if let url = URL(string: "climbhold://\(hold)") {
    NSWorkspace.shared.open(url)
}
