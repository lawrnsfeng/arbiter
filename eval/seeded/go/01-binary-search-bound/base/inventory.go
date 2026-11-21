// Package inventory tracks stocked item ids.
package inventory

import "sort"

// Inventory holds a sorted set of item ids.
type Inventory struct {
	ids []int
}

// New returns an Inventory holding ids, sorted ascending.
func New(ids ...int) *Inventory {
	s := append([]int(nil), ids...)
	sort.Ints(s)
	return &Inventory{ids: s}
}

// Has reports whether id is stocked.
func (inv *Inventory) Has(id int) bool {
	for _, v := range inv.ids {
		if v == id {
			return true
		}
	}
	return false
}
