package wordcount

import "testing"

func TestCount(t *testing.T) {
	got := Count([]string{"the cat The dog"})
	if got["the"] != 2 || got["cat"] != 1 || got["dog"] != 1 {
		t.Fatalf("got %v", got)
	}
}

func TestCountEmpty(t *testing.T) {
	if got := Count(nil); len(got) != 0 {
		t.Fatalf("got %v", got)
	}
}
