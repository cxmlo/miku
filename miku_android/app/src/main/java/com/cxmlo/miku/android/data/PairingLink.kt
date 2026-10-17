package com.cxmlo.miku.android.data

import java.net.URI
import java.net.URLDecoder
import java.nio.charset.StandardCharsets

data class PairingLink(val sessionId: String, val host: String) {
    companion object {
        fun parse(raw: String): PairingLink {
            val uri = URI(raw.trim())
            require(uri.scheme == "miku" && uri.host == "pair") {
                "Este no es un código QR de Miku."
            }

            val query = uri.rawQuery.orEmpty()
                .split("&")
                .mapNotNull { part ->
                    val pieces = part.split("=", limit = 2)
                    if (pieces.size != 2) return@mapNotNull null
                    URLDecoder.decode(pieces[0], StandardCharsets.UTF_8.name()) to
                        URLDecoder.decode(pieces[1], StandardCharsets.UTF_8.name())
                }
                .toMap()

            val sessionId = query["s"]?.takeIf(String::isNotBlank)
                ?: throw IllegalArgumentException("El QR no contiene una sesión de vinculación.")
            val host = query["ip"]?.takeIf(String::isNotBlank)
                ?: throw IllegalArgumentException("El QR no contiene la dirección del servidor.")
            require(host.matches(Regex("[a-zA-Z0-9.:%_-]+"))) {
                "La dirección del servidor no es válida."
            }
            val address = host.substringBefore(':').lowercase()
            require(
                address != "localhost" &&
                    address != "127.0.0.1" &&
                    address != "0.0.0.0" &&
                    host.lowercase() != "::1",
            ) {
                "El QR apunta a una dirección local del teléfono. Genera un QR nuevo desde Miku Desktop."
            }
            return PairingLink(sessionId, host)
        }
    }
}
