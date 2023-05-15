package com.itmo.recycleid.services

import com.google.common.cache.CacheBuilder
import com.google.common.cache.CacheLoader
import com.google.common.cache.LoadingCache
import com.itmo.recycleid.dtos.DeterminingRequestDTO
import com.itmo.recycleid.dtos.DeterminingResultsDTO
import com.itmo.recycleid.models.RecycleType
import com.itmo.recycleid.repositories.RecycleTypeRepository
import com.itmo.recycleid.services.ml.MlInternalWebService
import com.itmo.recycleid.services.storage.StorageService
import org.springframework.core.io.Resource
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile
import java.util.*
import java.util.concurrent.TimeUnit

@Service
class RecycleTypeDeterminingService(
    private val recycleTypeRepository: RecycleTypeRepository,
    private val mlWebService: MlInternalWebService,
    private val storageService: StorageService
) {
    var recycleTypesCache: LoadingCache<String, RecycleType> = CacheBuilder
        .newBuilder()
        .expireAfterAccess(1, TimeUnit.MINUTES)
        .build(object : CacheLoader<String, RecycleType>() {
            override fun load(key: String): RecycleType {
                recycleTypeRepository.findByCode(key)?.let {
                    return it
                }
                return RecycleType(description = "", code = key)
            }
        })

    fun createNewDeterminingRequest(imageFile: MultipartFile): DeterminingRequestDTO {
        val requestId = Random().nextInt(Int.MAX_VALUE)
        storageService.saveFile(imageFile, requestId)
        mlWebService.putIntoMlQueue(requestId, storageService.getFileUrl(requestId))
        return DeterminingRequestDTO(requestId)
    }

    fun getRequestImage(requestId: Int): Resource {
        return storageService.getFile(requestId)
    }

    fun getDeterminingResults(requestId: Int): DeterminingResultsDTO {
        val resultsDTO = mlWebService.getMlResults(requestId)
        if (!resultsDTO.areReady) {
            return resultsDTO
        }

        return enrichDeterminingResults(resultsDTO)
    }

    fun enrichDeterminingResults(resultsDTO: DeterminingResultsDTO): DeterminingResultsDTO {
        resultsDTO.recycleTypes.map { it.description = recycleTypesCache.get(it.code).description }
        return resultsDTO
    }
}
