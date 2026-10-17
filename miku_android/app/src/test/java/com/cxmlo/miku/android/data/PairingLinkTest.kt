package com.cxmlo.miku.android.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class PairingLinkTest {
    @Test
    fun parsesDesktopPairingQr() {
        val link = PairingLink.parse("miku://pair?s=ab12cd34&ip=192.168.1.25")

        assertEquals("ab12cd34", link.sessionId)
        assertEquals("192.168.1.25", link.host)
    }

    @Test
    fun rejectsDifferentQrScheme() {
        assertThrows(IllegalArgumentException::class.java) {
            PairingLink.parse("https://example.com/?s=abc&ip=192.168.1.25")
        }
    }

    @Test
    fun rejectsMissingPairingSession() {
        assertThrows(IllegalArgumentException::class.java) {
            PairingLink.parse("miku://pair?ip=192.168.1.25")
        }
    }

    @Test
    fun rejectsLoopbackHostThatCannotReachTheDesktopFromThePhone() {
        assertThrows(IllegalArgumentException::class.java) {
            PairingLink.parse("miku://pair?s=ab12cd34&ip=127.0.0.1")
        }
    }
}
