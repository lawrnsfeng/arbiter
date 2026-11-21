package config

import (
	"os"
	"path/filepath"
	"testing"
)

func write(t *testing.T, name, body string) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), name)
	if err := os.WriteFile(p, []byte(body), 0o600); err != nil {
		t.Fatal(err)
	}
	return p
}

func TestLoad(t *testing.T) {
	p := write(t, "app.conf", "# comment\nport = 8080\nhost=localhost\n")
	cfg, err := Load(p)
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Values["port"] != "8080" || cfg.Values["host"] != "localhost" {
		t.Fatalf("got %v", cfg.Values)
	}
}

func TestLoadMissing(t *testing.T) {
	if _, err := Load(filepath.Join(t.TempDir(), "nope.conf")); err == nil {
		t.Fatal("want error for missing file")
	}
}

func TestLoadBadLine(t *testing.T) {
	p := write(t, "bad.conf", "port\n")
	if _, err := Load(p); err == nil {
		t.Fatal("want error for line without '='")
	}
}
