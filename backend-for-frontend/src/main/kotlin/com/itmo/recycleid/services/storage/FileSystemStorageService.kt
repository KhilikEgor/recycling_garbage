package com.itmo.recycleid.services.storage

import org.springframework.core.io.Resource
import org.springframework.core.io.UrlResource
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.pathString

@Service
class FileSystemStorageService : StorageService {

    private val rootLocation: Path = Path.of("../files")

    override fun saveFile(file: MultipartFile, fileId: Int) {
        try {
            if (file.isEmpty || rootLocation == null) {
                throw RuntimeException("Failed to store empty file ${file.originalFilename}")
            }
            Files.copy(file.inputStream, this.rootLocation.resolve("img_$fileId"))
        } catch (e: IOException) {
            throw RuntimeException("Failed to store file ${file.originalFilename} with id $fileId", e)
        }
    }

    override fun getFile(fileId: Int): Resource {
        if (rootLocation == null) {
            throw RuntimeException("Failed to load resources")
        }

        val file = rootLocation.resolve("img_$fileId")
        val resource: Resource = UrlResource(file.toUri())

        if (resource.exists() || resource.isReadable) {
            return resource
        }

        throw RuntimeException("Could not read file: $fileId")
    }

    override fun getFileUrl(fileId: Int): String {
        if (rootLocation == null) {
            throw RuntimeException("Failed to load resources")
        }

        return rootLocation.resolve("img_$fileId").pathString
    }
}
