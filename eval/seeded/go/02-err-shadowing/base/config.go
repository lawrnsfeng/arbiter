// Package config loads key=value configuration files.
package config

import (
	"fmt"
	"os"
	"strings"
)

// Config is the parsed configuration.
type Config struct {
	Values map[string]string
}

// Load reads and parses the file at path.
func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("config: read %s: %w", path, err)
	}
	cfg := &Config{Values: map[string]string{}}
	if err := parse(data, cfg); err != nil {
		return nil, fmt.Errorf("config: parse %s: %w", path, err)
	}
	return cfg, nil
}

func parse(data []byte, cfg *Config) error {
	for i, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			return fmt.Errorf("line %d: missing '='", i+1)
		}
		cfg.Values[strings.TrimSpace(k)] = strings.TrimSpace(v)
	}
	return nil
}
