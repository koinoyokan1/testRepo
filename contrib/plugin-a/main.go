package main

import (
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()
	
	r.GET("/plugin-a/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"plugin": "A",
			"status": "healthy",
		})
	})
	
	r.Run(":8081")
}
