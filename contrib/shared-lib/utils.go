package sharedlib

// Shared library that doesn't depend on gin

type Config struct {
	Name    string
	Version string
}

func NewConfig(name, version string) *Config {
	return &Config{
		Name:    name,
		Version: version,
	}
}

func (c *Config) GetFullName() string {
	return c.Name + " v" + c.Version
}
