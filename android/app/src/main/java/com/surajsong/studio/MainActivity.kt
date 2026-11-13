package com.surajsong.studio

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    SurajSongHome()
                }
            }
        }
    }
}

@Composable
private fun SurajSongHome() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val preferences = remember { context.getSharedPreferences("surajsong", android.content.Context.MODE_PRIVATE) }
    var backendUrl by remember { mutableStateOf(preferences.getString("backend_url", "") ?: "") }
    var topic by remember { mutableStateOf("") }
    var language by remember { mutableStateOf("bn") }
    var duration by remember { mutableIntStateOf(4) }
    var lyrics by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Connect your backend to start creating songs.") }
    var isGenerating by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("SurajSong", style = MaterialTheme.typography.headlineLarge)
        Text(
            "AI Music Studio · বাংলা ও हिंदी",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary
        )
        Text("একটি topic লিখুন। AI lyrics তৈরি করবে; music ও vocal worker পরের ধাপে যুক্ত হবে।")

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Backend connection", style = MaterialTheme.typography.titleLarge)
                OutlinedTextField(
                    value = backendUrl,
                    onValueChange = { backendUrl = it.trim(); preferences.edit().putString("backend_url", it.trim()).apply() },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Backend HTTPS URL") },
                    placeholder = { Text("https://your-api.example.com") },
                    singleLine = true
                )
                Text("API key এখানে দেবেন না। Gemini key শুধু backend environment variable-এ থাকবে.", style = MaterialTheme.typography.bodySmall)
            }
        }

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Create a new song", style = MaterialTheme.typography.titleLarge)
                OutlinedTextField(
                    value = topic,
                    onValueChange = { topic = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Song topic or idea") },
                    placeholder = { Text("যেমন: হারিয়ে যাওয়া ভালোবাসা") },
                    minLines = 3
                )
                Text("Language")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = language == "bn", onClick = { language = "bn" }, label = { Text("বাংলা") })
                    FilterChip(selected = language == "hi", onClick = { language = "hi" }, label = { Text("हिन्दी") })
                }
                Text("Song duration")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(3, 4, 5).forEach { minutes ->
                        FilterChip(
                            selected = duration == minutes,
                            onClick = { duration = minutes },
                            label = { Text("$minutes min") }
                        )
                    }
                }
                Text("Genre, mood and singer: automatic")
                Button(
                    onClick = {
                        if (backendUrl.isBlank() || topic.isBlank()) {
                            status = "Backend URL এবং song topic লিখুন।"
                        } else {
                            scope.launch {
                                isGenerating = true
                                lyrics = ""
                                status = "AI lyrics তৈরি হচ্ছে…"
                                try {
                                    val result = withContext(Dispatchers.IO) {
                                        requestLyrics(backendUrl, topic, language, duration)
                                    }
                                    lyrics = result.optString("lyrics")
                                    status = "Lyrics তৈরি হয়েছে। Music worker status: " +
                                        if (result.optBoolean("music_worker_configured")) "connected" else "not connected yet"
                                } catch (error: Exception) {
                                    status = error.message ?: "Request failed. Backend URL and server settings check করুন।"
                                } finally {
                                    isGenerating = false
                                }
                            }
                        }
                    },
                    enabled = !isGenerating,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (isGenerating) CircularProgressIndicator(modifier = Modifier.height(18.dp), strokeWidth = 2.dp)
                    else Text("Generate Lyrics")
                }
            }
        }

        Text(status, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)

        if (lyrics.isNotBlank()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Generated lyrics", style = MaterialTheme.typography.titleLarge)
                    Text(lyrics, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }

        SocialAccountsCard(preferences = preferences)

        Text("Studio roadmap", style = MaterialTheme.typography.titleLarge)
        StudioFeatureCard("Music + AI Vocal", "ACE-Step self-hosted GPU worker · original songs")
        StudioFeatureCard("AI Music Video", "ComfyUI images + FFmpeg MP4 rendering")
        StudioFeatureCard("YouTube Upload", "YouTube Data API v3 + OAuth consent")
        Spacer(Modifier.height(8.dp))
        Text(
            "Free-first: text generation may use a limited free API tier. Music and image generation require GPU compute; no unlimited free cloud GPU is assumed.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

private fun requestLyrics(baseUrl: String, topic: String, language: String, duration: Int): JSONObject {
    val normalized = baseUrl.trim().trimEnd('/')
    require(normalized.startsWith("https://")) { "Backend URL অবশ্যই https:// দিয়ে শুরু হতে হবে।" }
    val connection = (URL("$normalized/api/v1/songs").openConnection() as HttpURLConnection).apply {
        requestMethod = "POST"
        connectTimeout = 15000
        readTimeout = 120000
        doOutput = true
        setRequestProperty("Content-Type", "application/json; charset=utf-8")
    }
    try {
        val payload = JSONObject()
            .put("topic", topic)
            .put("language", language)
            .put("duration_minutes", duration)
        connection.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
        if (code !in 200..299) {
            val detail = try { JSONObject(body).optString("detail", body) } catch (_: Exception) { body }
            throw IllegalStateException("API $code: $detail")
        }
        return JSONObject(body)
    } finally {
        connection.disconnect()
    }
}


@Composable
private fun SocialAccountsCard(preferences: android.content.SharedPreferences) {
    var youtube by remember { mutableStateOf(preferences.getString("social_youtube", "") ?: "") }
    var facebook by remember { mutableStateOf(preferences.getString("social_facebook", "") ?: "") }
    var instagram by remember { mutableStateOf(preferences.getString("social_instagram", "") ?: "") }
    var x by remember { mutableStateOf(preferences.getString("social_x", "") ?: "") }
    var saved by remember { mutableStateOf(false) }

    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Social accounts", style = MaterialTheme.typography.titleLarge)
            Text("আপনার channel ও page link যোগ করুন। পরে video publish করার সময় এগুলো ব্যবহার করা যাবে।", style = MaterialTheme.typography.bodySmall)
            OutlinedTextField(value = youtube, onValueChange = { youtube = it; saved = false }, modifier = Modifier.fillMaxWidth(), label = { Text("YouTube channel URL") }, singleLine = true)
            OutlinedTextField(value = facebook, onValueChange = { facebook = it; saved = false }, modifier = Modifier.fillMaxWidth(), label = { Text("Facebook Page URL") }, singleLine = true)
            OutlinedTextField(value = instagram, onValueChange = { instagram = it; saved = false }, modifier = Modifier.fillMaxWidth(), label = { Text("Instagram profile URL") }, singleLine = true)
            OutlinedTextField(value = x, onValueChange = { x = it; saved = false }, modifier = Modifier.fillMaxWidth(), label = { Text("X (Twitter) profile URL") }, singleLine = true)
            Button(
                onClick = {
                    preferences.edit()
                        .putString("social_youtube", youtube.trim())
                        .putString("social_facebook", facebook.trim())
                        .putString("social_instagram", instagram.trim())
                        .putString("social_x", x.trim())
                        .apply()
                    saved = true
                },
                modifier = Modifier.fillMaxWidth()
            ) { Text("Save social links") }
            if (saved) Text("Social links saved on this device.", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodySmall)
            Text("Note: link save করা মানেই account connect বা auto-post চালু হওয়া নয়। Publishing-এর জন্য প্রতিটি platform-এর official authorization/API integration লাগবে.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun StudioFeatureCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
