package com.itmo.recycleid.dtos

data class DeterminingResultsDTO(
    val areReady: Boolean,
    val recycleTypes: List<RecycleTypeDTO>
)
