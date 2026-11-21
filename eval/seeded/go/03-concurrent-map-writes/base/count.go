// Package wordcount counts word frequencies across documents.
package wordcount

import "strings"

// Count returns how often each lower-cased word occurs across docs.
func Count(docs []string) map[string]int {
	counts := make(map[string]int)
	for _, doc := range docs {
		for _, w := range strings.Fields(doc) {
			counts[strings.ToLower(w)]++
		}
	}
	return counts
}
