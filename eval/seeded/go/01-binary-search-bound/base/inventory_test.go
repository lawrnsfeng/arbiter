package inventory

import "testing"

func TestHas(t *testing.T) {
	inv := New(5, 1, 3)
	cases := []struct {
		id   int
		want bool
	}{
		{1, true},
		{3, true},
		{5, true},
		{4, false},
		{0, false},
	}
	for _, c := range cases {
		if got := inv.Has(c.id); got != c.want {
			t.Errorf("Has(%d) = %v, want %v", c.id, got, c.want)
		}
	}
}
