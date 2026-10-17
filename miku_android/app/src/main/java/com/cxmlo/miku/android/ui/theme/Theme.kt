package com.cxmlo.miku.android.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

@Composable
fun MikuTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = MikuPalette.Accent,
            background = MikuPalette.Background,
            surface = MikuPalette.Surface,
            onBackground = MikuPalette.TextPrimary,
            onSurface = MikuPalette.TextPrimary,
            error = MikuPalette.Error,
        ),
        content = content,
    )
}
