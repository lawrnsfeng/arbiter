package geometry

import "testing"

func TestSq(t *testing.T) {
	if sq(-3) != 9 {
		t.Fatal(sq(-3))
	}
}

func TestDistance(t *testing.T) {
	if d := Distance(Point{0, 0}, Point{3, 4}); d != 5 {
		t.Fatal(d)
	}
}

func TestPerimeter(t *testing.T) {
	sq := []Point{{0, 0}, {1, 0}, {1, 1}, {0, 1}}
	if p := Perimeter(sq); p != 4 {
		t.Fatal(p)
	}
	if p := Perimeter(nil); p != 0 {
		t.Fatal(p)
	}
}
