// Package mathx holds small numeric helpers.
package mathx

    // Abs returns the absolute value of x.
func Abs[T ~int | ~int64 | ~float64](x T) T {
	var zero T
	if x < zero {
		return -x
	}
	return x
}
