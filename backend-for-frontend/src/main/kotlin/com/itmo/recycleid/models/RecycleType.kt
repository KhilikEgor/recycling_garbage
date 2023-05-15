package com.itmo.recycleid.models

import javax.persistence.Column
import javax.persistence.Entity
import javax.persistence.Table

@Entity
@Table(name = "types")
open class RecycleType(
    @Column(name = "code", unique = true)
    val code: String,

    @Column(name = "description", nullable = true)
    val description: String?

) : BaseAuditEntity<Long>()
