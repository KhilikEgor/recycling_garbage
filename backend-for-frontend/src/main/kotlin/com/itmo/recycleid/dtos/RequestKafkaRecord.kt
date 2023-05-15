package com.itmo.recycleid.dtos

data class RequestKafkaRecord(val messageId: String, val detectionId: Int, val imagePath: String)
