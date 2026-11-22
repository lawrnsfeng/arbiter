// Package user models application users.
package user

import "errors"

// ErrNotFound is returned when no user has the requested id.
var ErrNotFound = errors.New("user: not found")

// User is an application user.
type User struct {
	ID   int
	Name string
}
