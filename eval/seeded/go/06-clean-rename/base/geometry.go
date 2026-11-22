// Package geometry computes properties of plane shapes.
package geometry

import "math"

// Point is a point in the plane.
type Point struct{ X, Y float64 }

// Distance returns the Euclidean distance between p and q.
func Distance(p, q Point) float64 {
	return math.Sqrt(sq(q.X-p.X) + sq(q.Y-p.Y))
}

// Perimeter returns the length of the closed path through pts.
func Perimeter(pts []Point) float64 {
	var tot float64
	for i := range pts {
		tot += Distance(pts[i], pts[(i+1)%len(pts)])
	}
	return tot
}

func sq(x float64) float64 { return x * x }
