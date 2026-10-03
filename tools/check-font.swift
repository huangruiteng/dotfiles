import Foundation
import CoreText

let name = "MesloLGSNFM-Regular"
let names = CTFontManagerCopyAvailablePostScriptNames() as! [String]
let installed = names.contains(name)
let font = CTFontCreateWithName(name as CFString, 14, nil)
let chars: [UniChar] = [0xe0b0, 0xe0b1, 0xe0a0]
var glyphs = [CGGlyph](repeating: 0, count: chars.count)
let supported = CTFontGetGlyphsForCharacters(font, chars, &glyphs, chars.count)
let ok = installed && supported && !glyphs.contains(0)
let data = try JSONSerialization.data(withJSONObject: ["ok": ok, "font": name, "installed": installed, "powerline_glyphs": supported])
print(String(data: data, encoding: .utf8)!)
exit(ok ? 0 : 1)
