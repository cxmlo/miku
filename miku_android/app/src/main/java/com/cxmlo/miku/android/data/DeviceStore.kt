package com.cxmlo.miku.android.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

data class DeviceCredentials(
    val serverIp: String,
    val deviceId: String,
    val pcName: String,
    val tunnelUrl: String = "",
)

class DeviceStore(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences(
        "miku_device",
        Context.MODE_PRIVATE,
    )

    fun read(): DeviceCredentials? {
        val serverIp = preferences.getString(KEY_SERVER_IP, null) ?: return null
        val deviceId = preferences.getString(KEY_DEVICE_ID, null)?.let(::decrypt) ?: return null
        val pcName = preferences.getString(KEY_PC_NAME, null)?.let(::decrypt).orEmpty()
        val tunnelUrl = preferences.getString(KEY_TUNNEL_URL, null).orEmpty()
        return DeviceCredentials(serverIp, deviceId, pcName, tunnelUrl)
    }

    fun save(serverIp: String, deviceId: String, pcName: String, tunnelUrl: String = "") {
        preferences.edit()
            .putString(KEY_SERVER_IP, serverIp)
            .putString(KEY_DEVICE_ID, encrypt(deviceId))
            .putString(KEY_PC_NAME, encrypt(pcName))
            .putString(KEY_TUNNEL_URL, tunnelUrl)
            .apply()
    }

    fun clear() {
        preferences.edit().clear().apply()
    }

    private fun encrypt(value: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val encrypted = cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(cipher.iv + encrypted, Base64.NO_WRAP)
    }

    private fun decrypt(value: String): String {
        val payload = Base64.decode(value, Base64.NO_WRAP)
        require(payload.size > GCM_IV_LENGTH) { "Invalid encrypted device credential" }
        val iv = payload.copyOfRange(0, GCM_IV_LENGTH)
        val ciphertext = payload.copyOfRange(GCM_IV_LENGTH, payload.size)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), GCMParameterSpec(GCM_TAG_BITS, iv))
        return String(cipher.doFinal(ciphertext), Charsets.UTF_8)
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEY_STORE).apply { load(null) }
        (keyStore.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }

        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEY_STORE).run {
            init(
                KeyGenParameterSpec.Builder(
                    KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
                )
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setRandomizedEncryptionRequired(true)
                    .build(),
            )
            generateKey()
        }
    }

    private companion object {
        const val KEY_ALIAS = "miku.mobile.device"
        const val ANDROID_KEY_STORE = "AndroidKeyStore"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val KEY_SERVER_IP = "server_ip"
        const val KEY_DEVICE_ID = "device_id"
        const val KEY_PC_NAME = "pc_name"
        const val KEY_TUNNEL_URL = "tunnel_url"
        const val GCM_IV_LENGTH = 12
        const val GCM_TAG_BITS = 128
    }
}
