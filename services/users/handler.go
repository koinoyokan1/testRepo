package users

import (
	"github.com/gin-gonic/gin"
	"example.com/oldversion/pkg/database"
	"example.com/oldversion/pkg/utils"
)

func RegisterRoutes(r *gin.Engine) {
	userGroup := r.Group("/users")
	{
		userGroup.GET("/:id", getUser)
		userGroup.POST("/", createUser)
		userGroup.PUT("/:id", updateUser)
		userGroup.DELETE("/:id", deleteUser)
	}
}

func getUser(c *gin.Context) {
	c.JSON(200, gin.H{"user": "mock-user"})
}

func createUser(c *gin.Context) {
	c.JSON(201, gin.H{"created": true})
}

func updateUser(c *gin.Context) {
	c.JSON(200, gin.H{"updated": true})
}

func deleteUser(c *gin.Context) {
	c.JSON(204, nil)
}
