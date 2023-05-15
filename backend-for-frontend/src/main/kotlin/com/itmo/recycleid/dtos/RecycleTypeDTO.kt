package com.itmo.recycleid.dtos

import org.springframework.lang.Nullable

data class RecycleTypeDTO(
    val code: String,
    val name: String,
    val percent: Double,
    @Nullable
    var description: String?
)
