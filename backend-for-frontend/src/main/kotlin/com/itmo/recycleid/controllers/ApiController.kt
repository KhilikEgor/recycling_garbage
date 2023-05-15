package com.itmo.recycleid.controllers

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController

@RestController()
@RequestMapping("api/v1")
class ApiController {
    @GetMapping()
    fun index(): List<ApiMessage> = listOf(
        ApiMessage("RecycleId"),
        ApiMessage("v0.0.1")
    )
}

data class ApiMessage(val text: String)
