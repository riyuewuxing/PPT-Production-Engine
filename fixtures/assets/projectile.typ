// Migrated from the private PPT scientific-visualization proof as a public-safe fixture.
#import "@preview/cetz:0.5.2": canvas, draw
#import "../../engine/presets/presentation_science.typ": *

// Tight asset canvas: the PPT builder preserves aspect ratio when placing the preview.
#set page(width: auto, height: auto, margin: .35cm)

#canvas(length: 1.35cm, {
  p-axis((-.8, 0), (9.2, 0))
  p-axis((0, -3.3), (0, 0.8))
  p-curve((0, 0), (1.6, -.112), (0.533333, 0), (1.066667, -.037333))
  p-curve((1.6, -.112), (3.2, -.448), (2.133333, -.186667), (2.666667, -.298667))
  p-curve((3.2, -.448), (4.8, -1.008), (3.733333, -.597333), (4.266667, -.784))
  p-curve((4.8, -1.008), (6.4, -1.792), (5.333333, -1.232), (5.866667, -1.493333))
  p-curve((6.4, -1.792), (8, -2.8), (6.933333, -2.090667), (7.466667, -2.426667))
  p-point((0, 0))
  p-point((1.6, -.112))
  p-point((3.2, -.448))
  p-point((4.8, -1.008))
  p-point((6.4, -1.792))
  p-point((8, -2.8))
  p-vector((0, 0), (1.8, 0), color: blue)
  p-vector((3.2, -.448), (3.2, -1.698), color: orange)
  p-label((0.9, 0.32), p-math($v_0$, size: 22pt, color: blue))
  p-label((3.32, -1.548), p-math($a = g$, size: 20pt, color: orange))
  p-label((5.15, 0.35), p-math($y = -1/2 g t^2$, size: 20pt, color: ink))
  p-label((9.18, -.28), p-plain("x", size: 19pt, color: muted))
  p-label((-.3, 0.68), p-plain("y", size: 19pt, color: muted))
})
