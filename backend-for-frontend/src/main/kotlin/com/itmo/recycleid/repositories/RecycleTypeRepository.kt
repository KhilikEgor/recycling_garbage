package com.itmo.recycleid.repositories

import com.itmo.recycleid.models.RecycleType
import org.springframework.data.jpa.repository.JpaRepository

interface RecycleTypeRepository : JpaRepository<RecycleType, Long> {
    fun findByCode(code: String): RecycleType?
}
