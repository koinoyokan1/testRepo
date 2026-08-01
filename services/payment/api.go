package payment

import (
	"github.com/gin-gonic/gin"
)

type PaymentAPI struct {
	engine *gin.Engine
}

func NewPaymentAPI() *PaymentAPI {
	r := gin.New()
	r.Use(gin.Logger())
	r.Use(gin.Recovery())
	
	r.POST("/payment/charge", chargePayment)
	r.POST("/payment/refund", refundPayment)
	
	return &PaymentAPI{engine: r}
}

func chargePayment(c *gin.Context) {
	c.JSON(200, gin.H{"charged": true})
}

func refundPayment(c *gin.Context) {
	c.JSON(200, gin.H{"refunded": true})
}
