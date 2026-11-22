package user

import "testing"

func TestErrNotFound(t *testing.T) {
	if ErrNotFound.Error() != "user: not found" {
		t.Fatal(ErrNotFound)
	}
}
