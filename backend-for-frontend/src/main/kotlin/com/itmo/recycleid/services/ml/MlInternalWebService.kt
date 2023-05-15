package com.itmo.recycleid.services.ml

import com.google.gson.FieldNamingPolicy
import com.google.gson.GsonBuilder
import com.itmo.recycleid.dtos.DeterminingResultsDTO
import com.itmo.recycleid.dtos.MlResultDTO
import com.itmo.recycleid.dtos.MlServerResponseDTO
import com.itmo.recycleid.dtos.RecycleTypeDTO
import com.itmo.recycleid.dtos.RequestKafkaRecord
import org.apache.kafka.clients.producer.KafkaProducer
import org.apache.kafka.clients.producer.ProducerRecord
import org.apache.kafka.clients.producer.RecordMetadata
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.ResponseEntity
import org.springframework.stereotype.Component
import org.springframework.stereotype.Service
import org.springframework.web.client.HttpClientErrorException
import org.springframework.web.client.RestTemplate
import java.net.ConnectException
import java.net.URI
import java.util.*
import java.util.concurrent.Future

const val DEFAULT_ML_TOPIC = "detections"

// const val GROUP_ID
@Component
class MlServerProperties {
    @Value("\${ml-server.host}")
    lateinit var host: String

    @Value("\${ml-server.port}")
    lateinit var port: String
}

@Component
class KafkaProperties {
    @Value("\${kafka.key.serializer}")
    lateinit var keySerializer: String

    @Value("\${kafka.value.serializer}")
    lateinit var valueSerializer: String

    @Value("\${kafka.bootstrap.servers}")
    lateinit var bootstrapServers: String

    fun asMap(): Map<String, String> {
        val map = mutableMapOf<String, String>()
        map["key.serializer"] = this.keySerializer
        map["value.serializer"] = this.valueSerializer
        map["bootstrap.servers"] = this.bootstrapServers

        return map
    }
}

@Service
class MlInternalWebService(
    val mlServerProperties: MlServerProperties,
    val kafkaProperties: KafkaProperties
) {
    fun putIntoMlQueue(
        id: Int,
        pathToFile: String
    ) {
        val gson = GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create()

        val kafkaRecord: RequestKafkaRecord = RequestKafkaRecord(
            messageId = UUID.randomUUID().toString(),
            detectionId = id,
            imagePath = pathToFile
        )

        val producerRecord: ProducerRecord<String, String> = ProducerRecord(DEFAULT_ML_TOPIC, gson.toJson(kafkaRecord).toString())
        val producer = KafkaProducer<String, String>(kafkaProperties.asMap() as Map<String, Any>?)
        val future: Future<RecordMetadata> = producer.send(producerRecord)
        // add log
        println(" message sent to " + future.get().topic())
    }

    fun getMlResults(
        id: Int
    ): DeterminingResultsDTO {
        val restTemplate = RestTemplate()
        val fooResourceUrl = URI("http://${mlServerProperties.host}:${mlServerProperties.port}/detections/$id")

        try {
            val response: ResponseEntity<MlResultDTO> = restTemplate.getForEntity(
                fooResourceUrl,
                MlResultDTO::class.java
            )

            val types: List<RecycleTypeDTO> = response.body?.labels_preds
                ?.map { it as List<Any> }
                ?.filter { it.size >= 2 }
                ?.map { Pair(it[0] as String, it[1] as Double) }
                ?.map {
                    RecycleTypeDTO(
                        code = it.first,
                        name = it.first,
                        percent = it.second,
                        description = null
                    )
                }
                .orEmpty()

            return DeterminingResultsDTO(
                areReady = types.isNotEmpty(),
                recycleTypes = types
            )
        } catch (ex: HttpClientErrorException) {
            return DeterminingResultsDTO(
                areReady = false,
                recycleTypes = emptyList()
            )
        } catch (ex: ConnectException) {
            return DeterminingResultsDTO(
                areReady = false,
                recycleTypes = emptyList()
            )
        }

//        // TODO Rewrite to connect python service
//        val list = ArrayList<RecycleTypeDTO>()
//        list.add(
//            RecycleTypeDTO(
//                code = "ALU",
//                name = "ALU_41",
//                percent = 80.0F,
//                description = null
//            )
//        )
//        list.add(
//            RecycleTypeDTO(
//                code = "PET",
//                name = "PET_01",
//                percent = 10.0F,
//                description = null
//            )
//        )
//        list.add(
//            RecycleTypeDTO(
//                code = "PP",
//                name = "PP_05",
//                percent = 9.0F,
//                description = null
//            )
//        )
//        list.add(
//            RecycleTypeDTO(
//                code = "PAP",
//                name = "PAP_20",
//                percent = 1.0F,
//                description = null
//            )
//        )
    }
}
