package mathx

import "testing"

func TestAbs(t *testing.T) {
	if Abs(-2) != 2 || Abs(3) != 3 || Abs(-1.5) != 1.5 {
		t.Fatal("Abs wrong")
	}
}
