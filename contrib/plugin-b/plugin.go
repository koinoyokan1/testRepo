package main

import (
	"github.com/gin-gonic/gin"
)

type PluginB struct {
	router *gin.Engine
}

func NewPluginB() *PluginB {
	r := gin.Default()
	
	r.GET("/plugin-b/status", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"plugin": "B",
			"version": "1.0.0",
		})
	})
	
	return &PluginB{router: r}
}
