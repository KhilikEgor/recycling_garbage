package com.itmo.recycleid.services.storage

import org.springframework.core.io.Resource
import org.springframework.web.multipart.MultipartFile

interface StorageService {
    fun saveFile(file: MultipartFile, fileId: Int)

    fun getFile(fileId: Int): Resource

    fun getFileUrl(fileId: Int): String
}
