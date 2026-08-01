package main

import (
	"github.com/gin-gonic/gin"
	"example.com/oldversion/pkg/utils"
)

func main() {
	r := gin.Default()
	
	r.GET("/api/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "ok",
		})
	})
	
	r.Run(":8080")
}
