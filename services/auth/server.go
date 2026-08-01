package auth

import (
	"github.com/gin-gonic/gin"
	"example.com/oldversion/pkg/database"
)

type AuthServer struct {
	router *gin.Engine
}

func NewAuthServer() *AuthServer {
	r := gin.Default()
	
	r.POST("/auth/login", handleLogin)
	r.POST("/auth/logout", handleLogout)
	
	return &AuthServer{router: r}
}

func handleLogin(c *gin.Context) {
	c.JSON(200, gin.H{"token": "mock-token"})
}

func handleLogout(c *gin.Context) {
	c.JSON(200, gin.H{"status": "logged out"})
}
