package com.itmo.recycleid.controllers

import com.itmo.recycleid.dtos.DeterminingRequestDTO
import com.itmo.recycleid.dtos.DeterminingResultsDTO
import com.itmo.recycleid.services.RecycleTypeDeterminingService
import org.springframework.core.io.Resource
import org.springframework.http.ResponseEntity
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.ResponseBody
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.multipart.MultipartFile

@RestController
@RequestMapping("api/v1/image-determining")
@Validated
class RecycleTypeDeterminingController(
    private val recycleTypeDeterminingService: RecycleTypeDeterminingService
) {
    @PostMapping
    fun createNewRequest(
        @RequestParam("file") file: MultipartFile
    ): ResponseEntity<DeterminingRequestDTO> {
        val request = recycleTypeDeterminingService.createNewDeterminingRequest(file)
        return ResponseEntity.ok(request)
    }

    @GetMapping("/{request_id}/source-image")
    @ResponseBody
    fun getRequestImage(
        @PathVariable("request_id") requestId: Int
    ): ResponseEntity<Resource> {
        val imageResource = recycleTypeDeterminingService.getRequestImage(requestId)
        return ResponseEntity.ok(imageResource)
    }

    @GetMapping("/{request_id}")
    @ResponseBody
    fun getRequestResults(
        @PathVariable("request_id") requestId: Int
    ): ResponseEntity<DeterminingResultsDTO> {
        val resultsDTO = recycleTypeDeterminingService.getDeterminingResults(requestId)
        return ResponseEntity.ok(resultsDTO)
    }
}
