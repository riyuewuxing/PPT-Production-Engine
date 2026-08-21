// Shared presentation preset for deterministic CeTZ scientific diagrams.
#import "@preview/cetz:0.5.2": draw

#let bg = rgb("f8fbfd")
#let ink = rgb("102a43")
#let muted = rgb("829ab1")
#let teal = rgb("0eaaa4")
#let blue = rgb("2563eb")
#let orange = rgb("ef8354")
#let red-orange = rgb("d95d39")
#let gold = rgb("f6ad55")
#let construction = rgb("9fb3c8")

#let axis-width = 1.1pt
#let construction-width = .9pt
#let trajectory-width = 2.8pt
#let vector-width = 2.3pt
#let force-width = 2.5pt
#let point-radius = .11

#let p-line(start, finish, color: ink, width: construction-width, arrow: false) = {
  if arrow {
    draw.line(start, finish, stroke: color + width, mark: (end: "stealth", transform-shape: false))
  } else {
    draw.line(start, finish, stroke: color + width)
  }
}

#let p-curve(start, finish, control-a, control-b, color: teal, width: trajectory-width) = draw.bezier(start, finish, control-a, control-b, stroke: color + width)
#let p-axis(start, finish) = p-line(start, finish, color: muted, width: axis-width, arrow: true)
#let p-construction(start, finish, arrow: false) = p-line(start, finish, color: construction, width: construction-width, arrow: arrow)
#let p-vector(start, finish, color: blue, width: vector-width) = p-line(start, finish, color: color, width: width, arrow: true)
#let p-force(start, finish, color: red-orange) = p-line(start, finish, color: color, width: force-width, arrow: true)
#let p-point(at, color: gold) = draw.circle(at, radius: point-radius, fill: color, stroke: ink + .9pt)
#let p-label(at, body) = draw.content(at, body)
#let p-plain(value, size: 18pt, color: ink) = text(size: size, fill: color)[#value]
#let p-math(value, size: 20pt, color: ink) = text(size: size, fill: color)[#value]
#let p-particle(at, radius: .18, color: gold) = draw.circle(at, radius: radius, fill: color, stroke: ink + 1pt)
#let p-equal-time(at, color: gold) = draw.circle(at, radius: .075, fill: color, stroke: ink + .5pt)
