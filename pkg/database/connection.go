package database

// Mock database package - doesn't use gin directly

type DB struct {
	ConnectionString string
}

func NewDB(connStr string) *DB {
	return &DB{ConnectionString: connStr}
}

func (db *DB) Query(query string) ([]interface{}, error) {
	return nil, nil
}
